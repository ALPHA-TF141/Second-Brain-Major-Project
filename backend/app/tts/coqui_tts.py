from datetime import datetime
from pathlib import Path


class CoquiTTS:
    def __init__(self, storage_dir: str = "data/voice/tts"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._model = None
        self.last_error = ""

    def is_ready(self):
        return self._model is not None

    def load(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        if self._model:
            return self._model
        try:
            from TTS.api import TTS

            self._model = TTS(model_name=model_name)
            self.last_error = ""
            return self._model
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def synthesize(self, text: str, voice_model: str = "default"):
        model = self.load()
        if not model:
            return {"file_path": "", "error": self.last_error}
        file_path = self.storage_dir / f"reply_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.wav"
        model.tts_to_file(text=text[:1200], file_path=str(file_path))
        return {"file_path": str(file_path), "error": ""}


coqui_tts = CoquiTTS()
