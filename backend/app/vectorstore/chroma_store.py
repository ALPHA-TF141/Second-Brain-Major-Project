from pathlib import Path


class ChromaVectorStore:
    def __init__(self, persist_dir: str = "data/chroma", collection_name: str = "second_brain_memories"):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self.last_error = ""

    def is_ready(self):
        return self._collection is not None

    def collection(self):
        if self._collection:
            return self._collection
        try:
            import chromadb

            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(name=self.collection_name)
            self.last_error = ""
            return self._collection
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def upsert(self, ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
        collection = self.collection()
        if not collection:
            raise RuntimeError(f"ChromaDB unavailable: {self.last_error}")
        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, query_embedding: list[float], n_results: int = 8, where: dict | None = None):
        collection = self.collection()
        if not collection:
            raise RuntimeError(f"ChromaDB unavailable: {self.last_error}")
        return collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where)

    def delete(self, ids: list[str]):
        collection = self.collection()
        if collection:
            collection.delete(ids=ids)


chroma_store = ChromaVectorStore()
