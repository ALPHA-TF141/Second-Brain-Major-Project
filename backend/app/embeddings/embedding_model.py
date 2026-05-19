class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.last_error = ""

    def is_ready(self):
        return self._model is not None

    def load(self):
        if self._model:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self.last_error = ""
            return self._model
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def encode(self, texts: list[str]):
        model = self.load()
        if not model:
            raise RuntimeError(f"Embedding model unavailable: {self.last_error}")
        vectors = model.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]


embedding_model = EmbeddingModel()
