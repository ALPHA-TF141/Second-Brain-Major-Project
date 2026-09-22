"""
Local wake-word detection - "Hey Jarvis".
===========================================================================
100% offline. No account, no API key, no cloud, no per-request cost.

openWakeWord ships a pretrained `hey_jarvis` model, which is exactly the name
already built into this app's UI. Audio never leaves the machine: the model is a
small ONNX network that scores 80ms frames on the CPU.

DESIGN
------
* Optional dependency. If openwakeword / sounddevice are not installed the app
  still runs and Alt+J still works - the status endpoint simply reports why.
* Frames are read on a daemon thread and scored there; nothing blocks the API.
* `process_frame()` is public so the test suite can push synthetic audio through
  the exact same code path the microphone uses, with no real device.
* Debounce prevents a single utterance firing the wake event several times.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Dict, List, Optional

# openWakeWord expects 16kHz mono, 80ms chunks -> 1280 samples
SAMPLE_RATE = 16000
FRAME_SAMPLES = 1280
FRAME_MS = 80


class WakeWordListener:
    def __init__(self):
        self.enabled = False
        self.running = False
        self.last_error = ""
        self.model_name = "hey_jarvis"

        self._model = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.RLock()

        self._last_fired = 0.0
        self._score_history: deque = deque(maxlen=20)
        self._detections = 0
        self._on_wake: Optional[Callable[[Dict[str, Any]], None]] = None
        self._status_detail = "not started"
        self._load_via = ""
        self._model_keys: set = set()

    # ------------------------------------------------------------- lifecycle
    def deps_available(self) -> Dict[str, Any]:
        """Are the optional packages importable?"""
        missing: List[str] = []
        try:
            import openwakeword  # noqa: F401
        except Exception:
            missing.append("openwakeword")
        try:
            import sounddevice  # noqa: F401
        except Exception:
            missing.append("sounddevice")
        return {"available": not missing, "missing": missing}

    def _pretrained_path(self) -> Optional[str]:
        """Locate the shipped ONNX file, e.g. .../resources/models/hey_jarvis_v0.1.onnx"""
        try:
            import openwakeword
            from pathlib import Path

            models_dir = Path(openwakeword.__file__).parent / "resources" / "models"
            if not models_dir.is_dir():
                return None
            for candidate in sorted(models_dir.glob(f"{self.model_name}*.onnx")):
                return str(candidate)
        except Exception:
            pass
        return None

    def _load_model(self) -> bool:
        """
        Load the wake-word model.

        openWakeWord changed its constructor between releases:
          0.6+   Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
          0.4.x  Model(wakeword_model_paths=["/.../hey_jarvis_v0.1.onnx"])
          0.4.x  Model()  -> loads EVERY pretrained model
        We try them newest-first. Getting this wrong means the detector silently
        never loads, which is exactly the sort of "it just doesn't work" failure
        that is painful to debug on a user's machine.
        """
        if self._model is not None:
            return True

        try:
            import numpy as np
            from openwakeword.model import Model
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            self._status_detail = "openwakeword not importable"
            return False

        path = self._pretrained_path()
        attempts = [
            ("wakeword_models + onnx", lambda: Model(wakeword_models=[self.model_name],
                                                     inference_framework="onnx")),
            ("wakeword_models", lambda: Model(wakeword_models=[self.model_name])),
            ("wakeword_model_paths", (lambda: Model(wakeword_model_paths=[path])) if path else None),
            ("all pretrained", lambda: Model()),
        ]

        errors = []
        for label, builder in attempts:
            if builder is None:
                continue
            try:
                model = builder()
            except Exception as exc:
                errors.append(f"{label}: {type(exc).__name__}")
                continue

            # Warm up so the first real utterance is not swallowed by allocation.
            try:
                model.predict(np.zeros(FRAME_SAMPLES, dtype=np.int16))
            except Exception as exc:
                errors.append(f"{label} warmup: {type(exc).__name__}")
                continue

            self._model = model
            self._load_via = label
            self._model_keys = self._discover_keys(model)

            # If the configured phrase is not among the loaded models, say so
            # rather than scoring something else.
            if self._model_keys and self.model_name not in self._model_keys:
                self.last_error = (
                    f"'{self.model_name}' was not among the loaded models: "
                    f"{', '.join(sorted(self._model_keys))}"
                )
                self._model = None
                continue

            self.last_error = ""
            self._status_detail = f"model loaded ({label})"
            return True

        self.last_error = "Could not load any wake-word model. " + ("; ".join(errors) or "unknown cause")
        self._status_detail = "model failed to load"
        self._model = None
        return False

    @staticmethod
    def _discover_keys(model) -> set:
        try:
            return set(model.models.keys())   # 0.4.x exposes .models
        except Exception:
            return set()

    def start(self, on_wake: Callable[[Dict[str, Any]], None]) -> bool:
        """Begin listening. Returns False (with last_error set) if unavailable."""
        with self._lock:
            if self.running:
                return True

            self._on_wake = on_wake
            deps = self.deps_available()
            if not deps["available"]:
                self.last_error = (
                    f"Missing package(s): {', '.join(deps['missing'])}. "
                    "Install with: pip install openwakeword sounddevice"
                )
                self._status_detail = "dependencies missing"
                self.running = False
                return False

            if not self._load_model():
                self.running = False
                return False

            self._stop.clear()
            self._thread = threading.Thread(target=self._listen_loop, name="wake-word", daemon=True)
            self._thread.start()
            self.running = True
            self._status_detail = "listening"
            return True

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            self.running = False
            self._status_detail = "stopped"
            thread = self._thread
            self._thread = None
        if thread and thread.is_alive():
            thread.join(timeout=2.0)

    # ----------------------------------------------------------- audio loop
    def _listen_loop(self) -> None:
        try:
            import sounddevice as sd
        except Exception as exc:
            self.last_error = f"sounddevice unavailable: {exc}"
            self.running = False
            return

        try:
            with sd.InputStream(
                channels=1,
                samplerate=SAMPLE_RATE,
                blocksize=FRAME_SAMPLES,
                dtype="int16",
            ) as stream:
                while not self._stop.is_set():
                    try:
                        data, _overflow = stream.read(FRAME_SAMPLES)
                    except Exception as exc:
                        self.last_error = f"microphone read failed: {exc}"
                        break
                    self.process_frame(data)
        except Exception as exc:
            # Includes "no default input device" on machines without a mic.
            self.last_error = f"Could not open the microphone: {exc}"
            self._status_detail = "microphone unavailable"
            self.running = False

    # ------------------------------------------------------- scoring (public)
    def process_frame(self, frame) -> Optional[float]:
        """
        Score one 80ms frame. Returns the wake-word probability, and fires the
        callback when it crosses the threshold.

        Public on purpose: the test suite drives this with synthetic audio, so
        the logic under test is byte-for-byte what the microphone feeds.
        """
        if self._model is None:
            return None

        try:
            import numpy as np

            audio = np.asarray(frame, dtype=np.int16).reshape(-1)
        except Exception:
            return None

        if audio.size < FRAME_SAMPLES:
            audio = np.pad(audio, (0, FRAME_SAMPLES - audio.size))
        elif audio.size > FRAME_SAMPLES:
            audio = audio[:FRAME_SAMPLES]

        try:
            scores = self._model.predict(audio)
        except Exception as exc:
            self.last_error = f"prediction failed: {exc}"
            return None

        if not scores:
            return None

        score = scores.get(self.model_name)
        if score is None:
            # Only safe if a single model is loaded. Falling back to max() with
            # several loaded would let a DIFFERENT phrase ("alexa") trigger us.
            if len(self._model_keys) == 1:
                score = next(iter(scores.values()))
            elif not self._model_keys and len(scores) == 1:
                score = next(iter(scores.values()))
            else:
                self.last_error = (
                    f"score for '{self.model_name}' missing from the model output "
                    f"(keys: {', '.join(sorted(scores.keys()))[:120]})"
                )
                return None
        score = float(score)

        self._score_history.append(score)

        threshold = float(getattr(self, "threshold", 0.5))
        if score >= threshold:
            self._fire(score)
        return score

    def _fire(self, score: float) -> None:
        now = time.time()
        if now - self._last_fired < float(getattr(self, "debounce_seconds", 2.5)):
            return   # same utterance still ringing out
        self._last_fired = now
        self._detections += 1

        payload = {
            "type": "wake",
            "source": "wake_word",
            "model": self.model_name,
            "load_method": self._load_via,
            "score": round(score, 3),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        try:
            self._on_wake and self._on_wake(payload)
        except Exception as exc:
            self.last_error = f"wake callback failed: {exc}"

    # ------------------------------------------------------------- reporting
    def status(self) -> Dict[str, Any]:
        deps = self.deps_available()
        return {
            "enabled": self.enabled,
            "running": self.running,
            "available": deps["available"],
            "missing_packages": deps["missing"],
            "model": self.model_name,
            "threshold": float(getattr(self, "threshold", 0.5)),
            "debounce_seconds": float(getattr(self, "debounce_seconds", 2.5)),
            "detections": self._detections,
            "last_error": self.last_error,
            "detail": self._status_detail,
            "recent_scores": [round(s, 3) for s in list(self._score_history)[-5:]],
            "install_hint": (
                "" if deps["available"]
                else "pip install openwakeword sounddevice"
            ),
        }


wake_word_listener = WakeWordListener()
