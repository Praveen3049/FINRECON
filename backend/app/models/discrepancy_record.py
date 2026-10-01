from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Numeric, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class DiscrepancyRecord(Base):
    __tablename__ = "discrepancy_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("reconciliation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    match_id = Column(String(36), ForeignKey("reconciliation_matches.id", ondelete="CASCADE"), nullable=True, index=True)
    
    discrepancy_type = Column(String(50), nullable=False, index=True)  # AMOUNT, DATE, ENTITY, CURRENCY, STATUS, DUPLICATE_ENTRY, MISSING_ENTRY, CONFLICTING_DATA
    field_name = Column(String(50), nullable=False)  # amount, transaction_date, counterparty_name, etc.
    
    source_value = Column(String(255), nullable=True)
    matched_value = Column(String(255), nullable=True)
    difference_numeric = Column(Numeric(18, 4), nullable=True)
    difference_percentage = Column(Float, nullable=True)
    
    root_cause_category = Column(String(50), nullable=True)  # PROCESSING_FEE, T_PLUS_LAG, FX_RATE_SHIFT, DUPLICATE_WEBHOOK, UNRECORDED_EXPENSE
    severity = Column(String(20), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), nullable=False, default="OPEN", index=True)  # OPEN, UNDER_REVIEW, RESOLVED, WRITTEN_OFF, ESCALATED
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    case = relationship("ReconciliationCase", back_populates="discrepancies")
    match = relationship("ReconciliationMatch", back_populates="discrepancies")

    __table_args__ = (
        Index("idx_discrepancy_type_severity", "discrepancy_type", "severity"),
    )

    def __repr__(self):
        return f"<DiscrepancyRecord {self.discrepancy_type} ({self.field_name}: diff={self.difference_numeric})>"
