from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.models.user import User


class ConnectorCredential(Base):
    """
    Dedicated table in SQLite (second_brain.db) for persisting all third-party
    app connectors, credentials, passwords, and tokens permanently.
    Ensures connectors remain live and connected across app restarts without
    needing to be reconnected every session.
    """
    __tablename__ = "connector_credentials"
    __table_args__ = (UniqueConstraint("user_id", "service_key", name="uq_user_connector_key"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_key = Column(String(80), nullable=False, index=True)
    service_name = Column(String(120), nullable=False)
    account_identifier = Column(String(255), default="")
    secret_payload = Column(Text, default="")  # Secure encrypted or stored credentials/token
    status = Column(String(40), default="connected")  # connected, configured, error, paused
    is_live = Column(Boolean, default=True)
    category = Column(String(50), default="service")  # mail, calendar, code, ai, search
    config_metadata = Column(Text, default="{}")  # JSON string with port, sync settings, endpoints
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="connectors")
