"""
Proactive Voice - Jarvis speaks first.
===========================================================================
In the films JARVIS is not a search box. It is *there*, and it opens its mouth
when something matters: "Sir, you have a call." That is this module.

Where the text comes from
    The agents already detect things - mail deadlines, insight collisions, vault
    syncs. Those produce notification cards today. This turns the important ones
    into a short sentence that is SPOKEN aloud, and raises the orb so there is a
    face attached to the voice.

Controls that make it livable (a talking assistant that never shuts up is worse
than one that never speaks):
    * priority gate    - only announce at or above a threshold
    * quiet hours      - silence on a schedule, except for "critical"
    * cooldown         - per-source and global, so one busy source cannot flood
    * dedupe           - the same sentence never repeats within a window
    * history          - everything it said is recorded and reviewable
"""
from __future__ import annotations

import re
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

PRIORITY_ORDER = {"low": 0, "normal": 1, "medium": 1, "high": 2, "critical": 3}

# Spoken lines are kept short on purpose. A long sentence read aloud is
# annoying and slow; the detail belongs on screen.
MAX_SPOKEN_CHARS = 240


class ProactiveVoice:
    def __init__(self):
        self._lock = threading.RLock()
        self.history: List[Dict[str, Any]] = []
        self._last_spoken_at: float = 0.0
        self._last_by_source: Dict[str, float] = {}
        self._recent_lines: List[tuple] = []   # (timestamp, normalised text)
        self._broadcaster = None
        self.enabled = True
        self.paused_reason = ""

    # ------------------------------------------------------------ plumbing
    def set_broadcaster(self, broadcaster) -> None:
        """Injected at startup: an async callable taking the event dict."""
        self._broadcaster = broadcaster

    @staticmethod
    def _now_ts() -> float:
        import time

        return time.time()

    @staticmethod
    def _normalise(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()

    # ------------------------------------------------------------- settings
    def _config(self) -> Dict[str, Any]:
        from app.config import settings

        return {
            "enabled": bool(getattr(self, "enabled", True)) and bool(settings.voice_announce_enabled),
            "min_priority": str(settings.voice_announce_min_priority or "high").lower(),
            "quiet_hours": str(settings.voice_quiet_hours or ""),
            "cooldown": int(settings.voice_announce_cooldown_seconds or 90),
            "dedupe_minutes": int(settings.voice_announce_dedupe_minutes or 30),
        }

    @staticmethod
    def _in_quiet_hours(spec: str) -> bool:
        """
        `spec` looks like "23:00-07:00" and may wrap midnight.
        An empty or malformed value means "never quiet".
        """
        if not spec or "-" not in spec:
            return False
        try:
            start_raw, end_raw = spec.split("-", 1)
            start_h, start_m = (int(x) for x in start_raw.strip().split(":"))
            end_h, end_m = (int(x) for x in end_raw.strip().split(":"))
        except Exception:
            return False

        now = datetime.now()
        minute = now.hour * 60 + now.minute
        start = start_h * 60 + start_m
        end = end_h * 60 + end_m

        if start == end:
            return False
        if start < end:
            return start <= minute < end
        # wraps midnight, e.g. 23:00-07:00
        return minute >= start or minute < end

    # -------------------------------------------------------------- decision
    def should_announce(self, text: str, priority: str = "normal", source: str = "system") -> Dict[str, Any]:
        """Returns {allowed: bool, reason: str} - always explainable."""
        cfg = self._config()

        if not cfg["enabled"]:
            return {"allowed": False, "reason": "proactive voice is disabled"}

        if not (text or "").strip():
            return {"allowed": False, "reason": "nothing to say"}

        wanted = PRIORITY_ORDER.get(str(priority).lower(), 1)
        floor = PRIORITY_ORDER.get(cfg["min_priority"], 2)
        if wanted < floor:
            return {"allowed": False, "reason": f"priority '{priority}' below the '{cfg['min_priority']}' threshold"}

        now = self._now_ts()

        # Quiet hours, except for critical items - a security or deadline alert
        # at 2am is allowed to wake you.
        if str(priority).lower() != "critical" and self._in_quiet_hours(cfg["quiet_hours"]):
            return {"allowed": False, "reason": f"quiet hours ({cfg['quiet_hours']})"}

        # Dedupe: the identical sentence recently spoken.
        norm = self._normalise(text)
        window = cfg["dedupe_minutes"] * 60
        for spoken_at, previous in self._recent_lines:
            if previous == norm and (now - spoken_at) < window:
                return {"allowed": False, "reason": "already said this recently"}

        # Per-source cooldown, so one chatty mailbox cannot dominate.
        last = self._last_by_source.get(source, 0.0)
        if (now - last) < cfg["cooldown"]:
            remaining = int(cfg["cooldown"] - (now - last))
            return {"allowed": False, "reason": f"source '{source}' cooldown ({remaining}s left)"}

        return {"allowed": True, "reason": ""}

    # -------------------------------------------------------------- speaking
    def shorten(self, text: str) -> str:
        """Trim to something pleasant to hear, keeping whole sentences."""
        clean = re.sub(r"\s+", " ", (text or "").strip())
        if len(clean) <= MAX_SPOKEN_CHARS:
            return clean
        cut = clean[:MAX_SPOKEN_CHARS]
        for stop in (". ", "! ", "? "):
            index = cut.rfind(stop)
            if index > 80:
                return cut[: index + 1]
        return cut.rstrip() + "…"

    def announce(self, text: str, priority: str = "high", source: str = "system",
                 force: bool = False) -> Dict[str, Any]:
        """
        Speak a line if policy allows. Never raises: a failed announcement must
        not break the agent that produced it.
        """
        spoken = self.shorten(text)
        decision = {"allowed": True, "reason": "forced"} if force else self.should_announce(spoken, priority, source)

        record = {
            "text": spoken,
            "priority": str(priority).lower(),
            "source": source,
            "spoken": bool(decision["allowed"]),
            "skipped_reason": "" if decision["allowed"] else decision["reason"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        with self._lock:
            self.history.insert(0, record)
            self.history = self.history[:200]

            if decision["allowed"]:
                now = self._now_ts()
                self._last_spoken_at = now
                self._last_by_source[source] = now
                self._recent_lines.append((now, self._normalise(spoken)))
                self._recent_lines = self._recent_lines[-50:]

        if decision["allowed"] and self._broadcaster:
            try:
                self._broadcaster({
                    "type": "speak",
                    "text": spoken,
                    "priority": str(priority).lower(),
                    "source": source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "show_orb": True,
                })
            except Exception as exc:
                record["spoken"] = False
                record["skipped_reason"] = f"broadcast failed: {exc}"

        return record

    # ------------------------------------------------------------ reporting
    def status(self) -> Dict[str, Any]:
        cfg = self._config()
        return {
            "enabled": cfg["enabled"],
            "min_priority": cfg["min_priority"],
            "quiet_hours": cfg["quiet_hours"],
            "in_quiet_hours": self._in_quiet_hours(cfg["quiet_hours"]),
            "cooldown_seconds": cfg["cooldown"],
            "dedupe_minutes": cfg["dedupe_minutes"],
            "spoken_count": sum(1 for h in self.history if h.get("spoken")),
            "skipped_count": sum(1 for h in self.history if not h.get("spoken")),
            "last_spoken": next((h for h in self.history if h.get("spoken")), None),
            "broadcaster_ready": self._broadcaster is not None,
        }


proactive_voice = ProactiveVoice()
