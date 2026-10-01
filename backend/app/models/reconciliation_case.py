from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Numeric, Integer, DateTime, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReconciliationCase(Base):
    __tablename__ = "reconciliation_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="OPEN", index=True)  # OPEN, UNDER_REVIEW, RECONCILED, REJECTED, ESCALATED
    priority = Column(String(20), nullable=False, default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    primary_source_type = Column(String(30), nullable=False, index=True)
    
    total_variance_amount = Column(Numeric(18, 4), default=0.0)
    total_date_variance_days = Column(Integer, default=0)
    assigned_reviewer_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    matches = relationship("ReconciliationMatch", back_populates="case", cascade="all, delete-orphan")
    discrepancies = relationship("DiscrepancyRecord", back_populates="case", cascade="all, delete-orphan")
    manual_reviews = relationship("ManualReview", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_case_status_priority", "status", "priority"),
        Index("idx_case_created_status", "created_at", "status"),
    )

    def __repr__(self):
        return f"<ReconciliationCase {self.case_number}: {self.title} [{self.status}]>"
