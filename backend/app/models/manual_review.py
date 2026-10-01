from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class ManualReview(Base):
    __tablename__ = "manual_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("reconciliation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(String(36), ForeignKey("reconciliation_matches.id", ondelete="SET NULL"), nullable=True, index=True)
    
    reviewer_name = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # CONFIRM_MATCH, REJECT_MATCH, MARK_DUPLICATE, MARK_MISSING, MERGE_RECORDS, ESCALATE, ADD_NOTE
    previous_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    case = relationship("ReconciliationCase", back_populates="manual_reviews")

    __table_args__ = (
        Index("idx_review_action_reviewer", "action", "reviewer_name"),
    )

    def __repr__(self):
        return f"<ManualReview {self.action} by {self.reviewer_name} on Case {self.case_id}>"
