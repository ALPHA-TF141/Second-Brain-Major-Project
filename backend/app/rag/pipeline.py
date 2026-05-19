from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.llm.llm_client import llm_client
from app.models.conversation import Conversation, ConversationContext, Message, RetrievedMemory
from app.prompts.memory_prompt import memory_prompt_builder
from app.semantic_search.search_engine import semantic_search_engine


class RAGPipeline:
    def get_or_create_conversation(self, db: Session, user_id: int, conversation_id: int | None, mode: str):
        if conversation_id:
            existing = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
            if existing:
                existing.mode = mode or existing.mode
                db.commit()
                return existing

        conversation = Conversation(user_id=user_id, title="Memory Chat", mode=mode or "summary")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    def retrieve(self, db: Session, question: str, mode: str):
        limit = settings.rag_context_limit
        if mode == "detailed":
            limit = min(12, limit + 4)
        results = semantic_search_engine.hybrid_search(db, question, limit=limit)
        context_items = []
        for item in results:
            memory = item["memory"]
            context_items.append(
                {
                    "memory_id": memory.id,
                    "title": memory.title,
                    "content": memory.content[:1100],
                    "source_type": memory.source_type,
                    "app_source": memory.app_source,
                    "session_id": memory.session_id,
                    "screenshot_id": memory.screenshot_id,
                    "timestamp": memory.created_at,
                    "score": item["score"],
                }
            )
        return context_items

    def history(self, db: Session, conversation_id: int):
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(30)
            .all()
        )
        return [{"role": row.role, "content": row.content} for row in rows]

    async def answer_stream(self, db: Session, user_id: int, question: str, conversation_id: int | None, mode: str):
        conversation = self.get_or_create_conversation(db, user_id, conversation_id, mode)
        user_message = Message(conversation_id=conversation.id, role="user", content=question)
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        context_items = self.retrieve(db, question, conversation.mode)
        for item in context_items:
            db.add(
                RetrievedMemory(
                    conversation_id=conversation.id,
                    message_id=user_message.id,
                    memory_id=item["memory_id"],
                    score=str(round(float(item["score"]), 4)),
                )
            )
        db.commit()

        history = self.history(db, conversation.id)
        prompt = memory_prompt_builder.build(question, context_items, history, conversation.mode)

        full_response = ""
        yield {"type": "conversation", "conversation_id": conversation.id, "mode": conversation.mode}
        yield {"type": "references", "items": context_items}
        yield {"type": "typing", "status": "started"}

        async for token in llm_client.stream(prompt, context_items):
            full_response += token
            yield {"type": "token", "token": token}

        assistant_message = Message(conversation_id=conversation.id, role="assistant", content=full_response)
        db.add(assistant_message)
        conversation.updated_at = datetime.utcnow()
        if conversation.title == "Memory Chat":
            conversation.title = question[:80]
        self._update_context(db, conversation.id, question, full_response)
        db.commit()
        db.refresh(assistant_message)
        yield {"type": "done", "message_id": assistant_message.id}

    def _update_context(self, db: Session, conversation_id: int, question: str, answer: str):
        context = db.query(ConversationContext).filter(ConversationContext.conversation_id == conversation_id).first()
        if not context:
            context = ConversationContext(conversation_id=conversation_id)
            db.add(context)
        context.last_user_reference = question[:1000]
        context.short_context = f"User asked: {question[:400]}\nAssistant answered: {answer[:700]}"


rag_pipeline = RAGPipeline()
