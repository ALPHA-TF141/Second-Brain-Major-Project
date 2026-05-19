"""
Error handling and recovery for memory operations.
"""
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from app.models.memory import Memory

logger = logging.getLogger(__name__)


class MemoryError(Exception):
    """Base exception for memory-related errors."""
    pass


class MemoryNotFoundError(MemoryError):
    """Memory not found in database."""
    pass


class SessionReconstructionError(MemoryError):
    """Error during session reconstruction."""
    pass


class RelationshipBuildingError(MemoryError):
    """Error during relationship building."""
    pass


class MemoryErrorHandler:
    """Handle and recover from memory operation errors."""
    
    @staticmethod
    def handle_missing_memory(memory_id: int, db: Session) -> Memory | None:
        """Handle when a memory cannot be found."""
        try:
            logger.warning(f"Memory {memory_id} not found")
            # Try to find similar memory by content hash
            return None
        except Exception as e:
            logger.error(f"Error handling missing memory {memory_id}: {e}")
            raise MemoryNotFoundError(f"Memory {memory_id} not found")
    
    @staticmethod
    def handle_reconstruction_error(session_id: int, error: Exception, db: Session):
        """Log and recover from session reconstruction errors."""
        logger.error(f"Error reconstructing session {session_id}: {error}")
        # Mark session as having errors but don't fail entirely
        return {
            "session_id": session_id,
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
            "recovered": False
        }
    
    @staticmethod
    def handle_relationship_error(source_id: int, target_id: int, error: Exception) -> bool:
        """Handle errors during relationship creation."""
        logger.warning(f"Error creating relationship {source_id} -> {target_id}: {error}")
        # Don't fail the whole rebuild, just skip this relationship
        return False
    
    @staticmethod
    def validate_memory_content(content: str, title: str) -> tuple[bool, str]:
        """Validate memory content before storage."""
        if not content or not content.strip():
            return False, "Empty content"
        if not title or not title.strip():
            return False, "Empty title"
        if len(content) > 50000:
            return False, "Content too long (max 50000 chars)"
        if len(title) > 220:
            return False, "Title too long (max 220 chars)"
        return True, "OK"
    
    @staticmethod
    def safe_session_summary(session_id: int, db: Session):
        """Safely get session summary with fallback."""
        try:
            from app.models.memory import SessionSummary
            summary = db.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()
            return summary
        except Exception as e:
            logger.error(f"Error fetching session summary {session_id}: {e}")
            return None


error_handler = MemoryErrorHandler()
