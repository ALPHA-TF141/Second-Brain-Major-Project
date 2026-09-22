"""
Wake service - the single place that turns "Jarvis was called" into action.
===========================================================================
Both the local wake-word detector and the Alt+J hotkey converge here, so there is
exactly one code path to reason about and one thing to test.

What it does on a wake event:
  1. broadcasts `{type: "wake"}` over /ws/live, which the running window turns
     into "show the orb, start listening"
  2. optionally speaks a short acknowledgement

The wake word runs on a background thread with no asyncio loop, so the broadcast
is dispatched with `run_coroutine_threadsafe` onto the loop captured at startup.
Using `asyncio.get_event_loop()` from a worker thread would silently create a
useless second loop and the event would never reach the UI.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.agents.proactive_voice import proactive_voice
from app.config import settings
from app.integrations.wake_word import wake_word_listener
from app.websocket.manager import manager

_main_loop: Optional[asyncio.AbstractEventLoop] = None
_wake_count = 0
_last_wake: Optional[Dict[str, Any]] = None


def capture_loop() -> None:
    """Called once at startup, from inside the running event loop."""
    global _main_loop
    try:
        _main_loop = asyncio.get_running_loop()
    except RuntimeError:
        _main_loop = None


async def _broadcast(payload: Dict[str, Any]) -> None:
    try:
        await manager.broadcast(payload)
    except Exception:
        pass


def _dispatch(payload: Dict[str, Any]) -> None:
    """Send a payload to the UI from ANY thread."""
    if _main_loop and _main_loop.is_running():
        try:
            asyncio.run_coroutine_threadsafe(_broadcast(payload), _main_loop)
            return
        except Exception:
            pass

    # No loop captured (e.g. inside a sync test): run it inline if we can.
    try:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_broadcast(payload))
        finally:
            loop.close()
    except Exception:
        pass


async def trigger_wake(source: str = "wake_word", score: float = 1.0) -> Dict[str, Any]:
    """Announce that Jarvis was called."""
    global _wake_count, _last_wake

    _wake_count += 1
    payload = {
        "type": "wake",
        "source": source,
        "score": round(float(score), 3),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "count": _wake_count,
    }
    _last_wake = payload

    await _broadcast(payload)
    return {"wake": payload, "count": _wake_count}


def on_wake_detected(payload: Dict[str, Any]) -> None:
    """Thread-safe callback handed to the wake-word listener."""
    payload = {**payload, "type": "wake"}
    _dispatch(payload)

    global _last_wake
    _last_wake = payload


def start_wake_word() -> Dict[str, Any]:
    """Start the listener if enabled. Safe to call when unavailable."""
    if not settings.wake_word_enabled:
        return {"started": False, "reason": "wake word disabled in settings"}

    wake_word_listener.enabled = True
    wake_word_listener.model_name = settings.wake_word_model
    wake_word_listener.threshold = float(settings.wake_word_threshold)
    wake_word_listener.debounce_seconds = float(settings.wake_word_debounce_seconds)

    started = wake_word_listener.start(on_wake_detected)
    return {
        "started": started,
        "reason": "" if started else wake_word_listener.last_error,
        "status": wake_word_listener.status(),
    }


def stop_wake_word() -> None:
    wake_word_listener.stop()


def wake_status() -> Dict[str, Any]:
    return {
        "listener": wake_word_listener.status(),
        "wake_count": _wake_count,
        "last_wake": _last_wake,
    }


def wire_proactive_voice() -> None:
    """
    Give the announcer a way to reach the UI.

    It runs from agent threads as well as request handlers, so it uses the same
    thread-safe dispatcher as the wake event.
    """
    proactive_voice.set_broadcaster(_dispatch)
