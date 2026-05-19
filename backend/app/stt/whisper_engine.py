class WhisperSTT:
    def __init__(self):
        self._model = None
        self.last_error = ""

    def is_ready(self):
        return self._model is not None

    def load(self):
        if self._model:
            return self._model
        try:
            import whisper

            self._model = whisper.load_model("base")
            self.last_error = ""
            return self._model
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def transcribe(self, audio_path: str, language: str = "mixed"):
        model = self.load()
        if not model:
            return {"text": "", "language": language, "confidence": 0.0, "error": self.last_error}
        options = {}
        if language == "ta":
            options["language"] = "ta"
        elif language == "en":
            options["language"] = "en"
        result = model.transcribe(audio_path, **options)
        return {
            "text": (result.get("text") or "").strip(),
            "language": result.get("language") or language,
            "confidence": 0.8 if result.get("text") else 0.0,
            "error": "",
        }


whisper_stt = WhisperSTT()
