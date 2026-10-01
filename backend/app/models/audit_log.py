from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, Text, Index
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), nullable=False, index=True)  # TRANSACTION, CASE, MATCH, INVOICE, CRYPTO
    entity_id = Column(String(100), nullable=False, index=True)
    case_id = Column(String(36), nullable=True, index=True)
    
    actor_type = Column(String(30), nullable=False, index=True)  # SYSTEM_ENGINE, MANUAL_REVIEWER, AI_ASSISTANT
    actor_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # AUTO_MATCH_CREATED, MANUAL_OVERRIDE, STATUS_CHANGED, DISCREPANCY_FLAGGED
    
    old_state = Column(Text, nullable=True)  # JSON-encoded prior state
    new_state = Column(Text, nullable=True)  # JSON-encoded new state
    details = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    entry_hash = Column(String(64), nullable=True, index=True)
    prev_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_audit_entity_time", "entity_type", "entity_id", "timestamp"),
        Index("idx_audit_actor_time", "actor_type", "actor_id", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.entity_type}:{self.entity_id} by {self.actor_id} at {self.timestamp}>"
