import asyncio
import threading
from datetime import datetime
from pathlib import Path


def _run_async_in_thread(coro):
    """Run an async coroutine from a synchronous context that may already
    be inside a running event loop (e.g. a FastAPI WebSocket handler)."""
    result = {}

    def _runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result["value"] = loop.run_until_complete(coro)
        finally:
            loop.close()

    thread = threading.Thread(target=_runner)
    thread.start()
    thread.join()
    return result.get("value")


class CoquiTTS:
    def __init__(self, storage_dir: str = "data/voice/tts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._ready = False
        self.last_error = ""

    def is_ready(self):
        try:
            import edge_tts
            return True
        except Exception:
            return False

    def load(self, model_name: str = ""):
        try:
            import edge_tts
            self._ready = True
            self.last_error = ""
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def synthesize(self, text: str, voice_model: str = "default"):
        try:
            import edge_tts
        except Exception as exc:
            self.last_error = str(exc)
            return {"file_path": "", "error": self.last_error}

        voice = voice_model if voice_model != "default" else "en-US-ChristopherNeural"
        file_path = self.storage_dir / f"reply_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.mp3"

        async def _gen():
            communicate = edge_tts.Communicate(text[:1200], voice)
            await communicate.save(str(file_path))

        try:
            _run_async_in_thread(_gen())
            if file_path.exists() and file_path.stat().st_size > 0:
                return {"file_path": str(file_path), "error": ""}
            return {"file_path": "", "error": "TTS produced no output"}
        except Exception as exc:
            self.last_error = str(exc)
            return {"file_path": "", "error": str(exc)}


coqui_tts = CoquiTTS()