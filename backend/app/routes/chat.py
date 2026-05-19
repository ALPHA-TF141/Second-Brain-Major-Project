from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.conversation import Conversation, Message, RetrievedMemory
from app.models.user import User
from app.rag.pipeline import rag_pipeline
from app.schemas.conversation import ChatRequest, ConversationOut, MessageOut, RetrievedMemoryOut


router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(30)
        .all()
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not conversation:
        return []
    return db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()


@router.get("/conversations/{conversation_id}/retrieved", response_model=list[RetrievedMemoryOut])
def list_retrieved(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not conversation:
        return []
    return (
        db.query(RetrievedMemory)
        .filter(RetrievedMemory.conversation_id == conversation_id)
        .order_by(RetrievedMemory.created_at.desc())
        .limit(30)
        .all()
    )


@router.post("/ask")
async def ask_memory(payload: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    answer = ""
    references = []
    conversation_id = payload.conversation_id
    async for event in rag_pipeline.answer_stream(db, user.id, payload.question, payload.conversation_id, payload.mode):
        if event["type"] == "conversation":
            conversation_id = event["conversation_id"]
        elif event["type"] == "references":
            references = event["items"]
        elif event["type"] == "token":
            answer += event["token"]
    return {"conversation_id": conversation_id, "answer": answer, "references": references}
