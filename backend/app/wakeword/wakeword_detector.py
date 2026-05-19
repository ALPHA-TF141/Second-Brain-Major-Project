class WakeWordDetector:
    def is_wake_phrase(self, text: str, wake_words: list[str]):
        lowered = text.lower()
        return any(word.strip().lower() in lowered for word in wake_words if word.strip())

    def strip_wake_phrase(self, text: str, wake_words: list[str]):
        cleaned = text
        for word in wake_words:
            cleaned = cleaned.replace(word, "", 1)
            cleaned = cleaned.replace(word.lower(), "", 1)
        return cleaned.strip(" ,.!?")


wakeword_detector = WakeWordDetector()
