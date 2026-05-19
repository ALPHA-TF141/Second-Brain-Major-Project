import asyncio
from datetime import datetime

from app.database.session import SessionLocal
from app.embeddings.embedding_model import embedding_model
from app.models.memory import Memory
from app.models.semantic import EmbeddingJob, VectorMemory
from app.vectorstore.chroma_store import chroma_store


class EmbeddingWorker:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None
        self.is_running = False
        self.last_error = ""

    def start(self):
        if self.worker_task:
            return
        self.is_running = True
        self.worker_task = asyncio.create_task(self._run())

    async def enqueue(self, memory_id: int):
        await self.queue.put(memory_id)

    async def enqueue_unindexed(self):
        db = SessionLocal()
        try:
            indexed = {row.memory_id for row in db.query(VectorMemory.memory_id).all()}
            memory_ids = [row.id for row in db.query(Memory.id).all() if row.id not in indexed]
        finally:
            db.close()
        for memory_id in memory_ids:
            await self.enqueue(memory_id)
        return {"queued": len(memory_ids)}

    def status(self):
        return {
            "is_running": self.is_running,
            "queued": self.queue.qsize(),
            "embedding_model_ready": embedding_model.is_ready(),
            "vector_store_ready": chroma_store.is_ready(),
            "last_error": self.last_error or embedding_model.last_error or chroma_store.last_error,
        }

    async def _run(self):
        while True:
            memory_id = await self.queue.get()
            try:
                await asyncio.to_thread(self._index_memory, memory_id)
            except Exception as exc:
                self.last_error = str(exc)
            finally:
                self.queue.task_done()

    def _index_memory(self, memory_id: int):
        db = SessionLocal()
        job = EmbeddingJob(memory_id=memory_id, status="running", started_at=datetime.utcnow())
        db.add(job)
        db.commit()

        try:
            memory = db.query(Memory).filter(Memory.id == memory_id).first()
            if not memory:
                raise ValueError("Memory not found")

            text = f"{memory.title}\n{memory.topic_label}\n{memory.content}"
            embedding = embedding_model.encode([text])[0]
            vector_id = f"memory-{memory.id}"
            chroma_store.upsert(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[memory.content],
                metadatas=[
                    {
                        "memory_id": memory.id,
                        "session_id": memory.session_id,
                        "source_type": memory.source_type,
                        "app_source": memory.app_source,
                        "topic_label": memory.topic_label,
                        "created_at": memory.created_at.isoformat() if memory.created_at else "",
                    }
                ],
            )

            existing = db.query(VectorMemory).filter(VectorMemory.memory_id == memory.id).first()
            if not existing:
                existing = VectorMemory(memory_id=memory.id, vector_id=vector_id)
                db.add(existing)
            existing.collection_name = chroma_store.collection_name
            existing.embedding_model = embedding_model.model_name
            existing.dimensions = len(embedding)
            existing.indexed_at = datetime.utcnow()
            job.status = "completed"
            job.finished_at = datetime.utcnow()
            db.commit()
        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.add(job)
            db.commit()
            raise
        finally:
            db.close()


embedding_worker = EmbeddingWorker()
