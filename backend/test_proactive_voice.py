"""
Wake word + proactive voice regression test (offline).
===========================================================================
Proves the two things that turn an app into an assistant:

  1. "Hey Jarvis" -> the wake event reaches the UI (without a real microphone)
  2. Jarvis speaks first -> but ONLY when policy says it should

The wake-word scoring path is driven with synthetic frames through
`process_frame()`, which is the exact method the microphone loop calls. So the
logic under test is byte-for-byte what runs on real audio - no mocking of the
code under test, only of the audio arriving at it.

Usage (backend folder, venv active):
    python test_proactive_voice.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL = "[PASS]", "[FAIL]"
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  --> {PASS} {label}")
    else:
        failures.append(label)
        print(f"  --> {FAIL}  {label}   {detail}")


class FakeModel:
    """Stands in for the ONNX wake-word model: scores exactly what we tell it."""

    def __init__(self):
        self.next_score = 0.0
        self.calls = 0
        self.last_shape = None

    def predict(self, frame):
        self.calls += 1
        self.last_shape = getattr(frame, "size", None)
        return {"hey_jarvis": self.next_score}


def main():
    print("=" * 74)
    print("  JARVIS OS - WAKE WORD + PROACTIVE VOICE TEST (offline)")
    print("=" * 74)

    from app.config import settings
    from app.integrations.wake_word import FRAME_SAMPLES, wake_word_listener
    from app.agents.proactive_voice import proactive_voice

    # ---------------------------------------------------------------- setup
    settings.voice_announce_enabled = True
    settings.voice_announce_min_priority = "high"
    # Quiet hours are OFF for the body of this suite, on purpose.
    #
    # They used to be set to "23:00-07:00" here, and the policy compares that
    # window against the wall clock. So every section asserting that a line IS
    # spoken passed or failed depending on what time it was: run the verifier at
    # 23:30 and seven checks failed with "quiet hours (23:00-07:00)", even though
    # the code was correct. Same class of phantom failure as the timeouts fixed
    # elsewhere in this suite.
    #
    # Quiet hours are covered properly in section [6], which injects a window
    # that provably contains the current minute and asserts both that
    # non-critical lines are silenced and that critical ones break through - a
    # real behavioural test, with no dependence on when it runs.
    settings.voice_quiet_hours = ""
    settings.voice_announce_cooldown_seconds = 90
    settings.voice_announce_dedupe_minutes = 30

    # capture what would have been sent to the UI
    broadcasts = []
    import app.services.wake_service as wake_service

    def fake_broadcaster(payload):
        broadcasts.append(payload)

    proactive_voice.set_broadcaster(fake_broadcaster)
    proactive_voice.history.clear()
    proactive_voice.enabled = True

    # ------------------------------------------------- 1. dependency handling
    print("\n[1] Optional packages are handled honestly")
    deps = wake_word_listener.deps_available()
    check("deps_available() returns a verdict", "available" in deps and "missing" in deps,
          str(deps))
    status = wake_word_listener.status()
    check("status reports availability", "available" in status)
    check("status names the model", status["model"] == "hey_jarvis", status["model"])
    check("status gives an install hint when unavailable",
          deps["available"] or "pip install" in status["install_hint"],
          status["install_hint"])
    if not deps["available"]:
        print(f"      (openwakeword/sounddevice not installed here: {deps['missing']})")

    # --------------------------------------------- 2. scoring + threshold
    print("\n[2] Wake-word scoring and the threshold")
    model = FakeModel()
    wake_word_listener._model = model            # inject the fake audio model
    wake_word_listener.threshold = 0.5
    wake_word_listener.debounce_seconds = 0.0    # disable debounce for this section
    wake_word_listener._detections = 0

    fired = []
    wake_word_listener._on_wake = lambda payload: fired.append(payload)

    model.next_score = 0.10
    score = wake_word_listener.process_frame([0] * FRAME_SAMPLES)
    check("silence scores low and does NOT fire", score == 0.10 and not fired,
          f"score={score} fired={len(fired)}")

    model.next_score = 0.35
    wake_word_listener.process_frame([0] * FRAME_SAMPLES)
    check("a sub-threshold score does NOT fire", not fired, f"fired={len(fired)}")

    model.next_score = 0.87
    wake_word_listener.process_frame([0] * FRAME_SAMPLES)
    check("a score above the threshold FIRES", len(fired) == 1, f"fired={len(fired)}")
    check("the event carries the model and score",
          fired and fired[0]["model"] == "hey_jarvis" and fired[0]["score"] == 0.87,
          str(fired[:1]))
    check("the frame was the expected 80ms size", model.last_shape == FRAME_SAMPLES,
          f"got {model.last_shape}")

    # ------------------------------------------------- 3. debounce
    print("\n[3] One utterance must not fire several times")
    wake_word_listener.debounce_seconds = 5.0
    wake_word_listener._last_fired = 0.0   # past the debounce so the FIRST frame fires
    fired.clear()
    model.next_score = 0.95
    for _ in range(6):                     # six consecutive loud frames
        wake_word_listener.process_frame([0] * FRAME_SAMPLES)
    check("repeated loud frames fire the wake event exactly once",
          len(fired) == 1, f"fired {len(fired)} times")

    # ------------------------------------- 4. the event reaches the UI layer
    print("\n[4] The wake event reaches the UI broadcaster")
    # Capture the wake service's own broadcast, which is what the detector calls
    # from its worker thread. Faking the transport lets us assert the dispatch
    # without a live event loop or a connected client.
    wake_broadcasts = []
    original_broadcast = wake_service._broadcast

    async def fake_broadcast(payload):
        wake_broadcasts.append(payload)

    wake_service._broadcast = fake_broadcast
    try:
        wake_service.on_wake_detected({"type": "wake", "source": "wake_word", "score": 0.9})
        check("a wake payload was dispatched to the UI layer",
              any(b.get("type") == "wake" for b in wake_broadcasts),
              str(wake_broadcasts))
    finally:
        wake_service._broadcast = original_broadcast

    # --------------------------------------------- 5. proactive policy gates
    print("\n[5] Proactive voice only speaks when it should")
    from datetime import datetime

    # (a) priority floor
    allowed_high = proactive_voice.should_announce("Sir, deadline is Friday.", "high", "mail")
    check("a high-priority line is allowed", allowed_high["allowed"], allowed_high["reason"])

    allowed_low = proactive_voice.should_announce("Sir, a newsletter arrived.", "low", "mail")
    check("a low-priority line is refused", not allowed_low["allowed"], allowed_low["reason"])
    check("and the refusal explains itself", "threshold" in allowed_low["reason"], allowed_low["reason"])

    # (b) cooldown after speaking
    proactive_voice._last_by_source.clear()
    broadcasts.clear()
    proactive_voice.announce("Sir, first deadline found.", "high", "mail")
    check("the first line is spoken", any(b.get("type") == "speak" for b in broadcasts),
          str(broadcasts))

    broadcasts.clear()
    second = proactive_voice.announce("Sir, a completely different deadline.", "high", "mail")
    check("a second line from the SAME source is held back by the cooldown",
          not second["spoken"] and "cooldown" in second["skipped_reason"],
          second["skipped_reason"])
    check("nothing was broadcast for the held-back line", not broadcasts, str(broadcasts))

    # (c) a different source is not blocked by another's cooldown
    third = proactive_voice.announce("Sir, an insight collision formed.", "high", "insight")
    check("a different source is not blocked by another's cooldown",
          third["spoken"], third["skipped_reason"])

    # (d) quiet hours
    print("\n[6] Quiet hours")
    original_quiet = settings.voice_quiet_hours
    now = datetime.now()
    # build a window that definitely contains the current minute
    start = f"{(now.hour - 1) % 24:02d}:00"
    end = f"{(now.hour + 1) % 24:02d}:59"
    settings.voice_quiet_hours = f"{start}-{end}"
    check("a wrapping quiet-hours window is detected",
          proactive_voice._in_quiet_hours(settings.voice_quiet_hours)
          or proactive_voice._in_quiet_hours(f"{start}-{end}"),
          f"{start}-{end}")

    denied = proactive_voice.should_announce("Sir, something happened.", "high", "other")
    check("non-critical lines are silenced during quiet hours",
          not denied["allowed"] and "quiet" in denied["reason"], denied["reason"])

    critical = proactive_voice.should_announce("Sir, a security alert.", "critical", "other")
    check("CRITICAL lines break through quiet hours", critical["allowed"], critical["reason"])

    settings.voice_quiet_hours = ""
    check("an empty quiet-hours setting means never quiet",
          not proactive_voice._in_quiet_hours(""))
    settings.voice_quiet_hours = original_quiet

    # (e) dedupe
    print("\n[7] It must not repeat itself")
    proactive_voice._last_by_source.clear()
    proactive_voice._recent_lines.clear()
    broadcasts.clear()
    proactive_voice.announce("Sir, the AQI report is missing.", "high", "insight")
    check("the line is spoken once", len([b for b in broadcasts if b.get("type") == "speak"]) == 1)

    proactive_voice._last_by_source.clear()          # bypass the cooldown only
    repeat = proactive_voice.announce("Sir, the AQI report is missing!", "high", "insight")
    check("the SAME sentence is not repeated", not repeat["spoken"], repeat["skipped_reason"])
    check("the dedupe reason is reported", "already said" in repeat["skipped_reason"],
          repeat["skipped_reason"])

    # ---------------------------------------------- 8. spoken text is sane
    print("\n[8] Spoken lines stay short enough to listen to")
    long_text = "Sir, " + ("this is a very long sentence about deadlines. " * 20)
    shortened = proactive_voice.shorten(long_text)
    check("long text is shortened", len(shortened) <= 245, f"{len(shortened)} chars")
    check("shortening keeps whole sentences", shortened.endswith((".", "…")), shortened[-40:])
    check("short text is left alone",
          proactive_voice.shorten("Sir, ready.") == "Sir, ready.")

    # ------------------------------------------------- 9. API surface
    print("\n[9] API surface")
    from fastapi.testclient import TestClient

    from app.main import app

    api = TestClient(app)
    token = api.post("/api/auth/login", json={
        "username": "Immanuel", "password": "secondbrain", "device_name": "test"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = api.get("/api/proactive/status", headers=headers)
    check("status endpoint works", r.status_code == 200, r.text[:160])
    body = r.json()
    check("reports wake word readiness", "wake_word" in body and "running" in body["wake_word"])
    check("reports voice policy", body["voice"]["min_priority"] == "high",
          str(body["voice"].get("min_priority")))

    r = api.post("/api/proactive/wake/test", headers=headers)
    check("wake test endpoint works", r.status_code == 200, r.text[:160])
    check("wake test reports a wake event", r.json().get("wake", {}).get("type") == "wake",
          r.text[:160])

    r = api.post("/api/proactive/announce", headers=headers,
                 json={"text": "Sir, this is a test.", "priority": "high", "force": True})
    check("manual announce works", r.status_code == 200 and r.json().get("spoken") is True,
          r.text[:160])

    r = api.post("/api/proactive/announce", headers=headers, json={"text": "   "})
    check("empty announce is rejected", r.status_code == 400, f"got {r.status_code}")

    r = api.get("/api/proactive/history", headers=headers)
    check("history is recorded", r.status_code == 200 and len(r.json()) > 0,
          f"{len(r.json())} entries")

    r = api.post("/api/proactive/pause", headers=headers)
    check("pause works", r.status_code == 200 and r.json()["paused"] is True)
    blocked = api.post("/api/proactive/announce", headers=headers,
                       json={"text": "should not speak", "priority": "high", "force": False})
    check("paused voice refuses to speak",
          blocked.json().get("spoken") is False, blocked.text[:120])
    r = api.post("/api/proactive/resume", headers=headers)
    check("resume works", r.status_code == 200 and r.json()["paused"] is False)

    r = api.get("/api/proactive/status")
    check("status requires the app JWT", r.status_code == 401, f"got {r.status_code}")

    # --------------------------------------------- 10. end-to-end: deadline
    print("\n[10] End-to-end: a mail deadline becomes a spoken line")
    broadcasts.clear()
    proactive_voice.history.clear()
    proactive_voice._last_by_source.clear()
    proactive_voice._recent_lines.clear()

    from app.agents.mail_ingestion_agent import mail_ingestion_agent

    mail_ingestion_agent._notify_actions(
        [{"kind": "deadline", "title": "Deadline: IEEE conference draft deadline",
          "due_date": "2026-09-25", "priority": "high", "trigger": "deadline"}],
        {"from": "Prof. Sharma <sharma@university.edu>", "subject": "IEEE draft deadline"},
        "vtu24334@veltech.edu.in",
    )

    spoken = [b for b in broadcasts if b.get("type") == "speak"]
    check("the deadline was spoken, not just filed", len(spoken) == 1, str(broadcasts)[:200])
    if spoken:
        text = spoken[0]["text"]
        check("the spoken line names the deadline", "IEEE conference draft deadline" in text, text)
        check("the spoken line names the sender", "sharma@university.edu" in text, text)
        check("the spoken line includes the due date", "2026-09-25" in text, text)
        check("it opens with Sir", text.startswith("Sir,"), text)
        check("the orb is told to appear", spoken[0].get("show_orb") is True)

    # ---------------------------- 11. real model, real API (version drift)
    print("\n[11] Real openWakeWord model loads and scores correctly")
    # Drop the injected FakeModel first, otherwise _load_model() short-circuits
    # on it and this section would silently test the fake instead of the real one.
    wake_word_listener._model = None
    wake_word_listener._model_keys = set()
    wake_word_listener._load_via = ""
    real_ok = wake_word_listener._load_model()
    if not real_ok:
        deps_now = wake_word_listener.deps_available()
        if deps_now["available"]:
            # Installed but unusable is a genuine failure worth shouting about.
            check("the installed openWakeWord can be loaded", False,
                  wake_word_listener.last_error)
        else:
            print(f"      SKIP - openWakeWord not installed ({', '.join(deps_now['missing'])}).")
            print("      Install with: pip install openwakeword sounddevice")
    else:
        check("a model loaded", True)
        check("it loaded hey_jarvis", "hey_jarvis" in (wake_word_listener._model_keys or {"hey_jarvis"}),
              str(sorted(wake_word_listener._model_keys)))
        print(f"      load method: {wake_word_listener._load_via}")

        # Negative control through the same code path the microphone uses.
        wake_word_listener.debounce_seconds = 0.0
        wake_word_listener.threshold = 0.5
        fired.clear()
        loudest = 0.0
        import numpy as _np

        for label, audio in [
            ("silence", _np.zeros(16000, dtype=_np.int16)),
            ("noise", _np.random.default_rng(1).normal(0, 300, 16000).astype(_np.int16)),
            ("tone", (_np.sin(2 * _np.pi * 440 * _np.arange(16000) / 16000) * 8000).astype(_np.int16)),
        ]:
            for i in range(0, len(audio) - FRAME_SAMPLES, FRAME_SAMPLES):
                score = wake_word_listener.process_frame(audio[i:i + FRAME_SAMPLES])
                if score:
                    loudest = max(loudest, score)

        check("silence / noise / tone never trigger the wake word",
              not fired and loudest < 0.2, f"peak={loudest:.4f} fired={len(fired)}")

    # cleanup the injected model so a later test importing this module is sane
    wake_word_listener._model = None
    wake_word_listener._on_wake = None
    wake_word_listener.debounce_seconds = 2.5
    proactive_voice.set_broadcaster(None)

    print("\n" + "=" * 74)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 74)
        return 1
    print("  ALL WAKE WORD + PROACTIVE VOICE CHECKS PASSED")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
