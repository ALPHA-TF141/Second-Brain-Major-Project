class SimpleVAD:
    def __init__(self, min_chunk_bytes: int = 1200):
        self.min_chunk_bytes = min_chunk_bytes

    def has_voice(self, audio_bytes: bytes):
        return len(audio_bytes or b"") >= self.min_chunk_bytes


simple_vad = SimpleVAD()
