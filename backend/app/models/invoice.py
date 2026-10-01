from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    entity_id = Column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    issuer_name = Column(String(150), nullable=False)
    recipient_name = Column(String(150), nullable=False, index=True)
    recipient_email = Column(String(100), nullable=True)
    
    total_amount = Column(Numeric(18, 4), nullable=False, index=True)
    paid_amount = Column(Numeric(18, 4), nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default="USD")
    
    issue_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="ISSUED", index=True)  # ISSUED, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED
    
    reference_order_id = Column(String(100), nullable=True, index=True)
    crypto_wallet_dest = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    entity = relationship("Entity", back_populates="invoices")

    __table_args__ = (
        Index("idx_invoice_entity_date", "entity_id", "issue_date"),
        Index("idx_invoice_status_amount", "status", "total_amount"),
    )

    def __repr__(self):
        return f"<Invoice {self.invoice_number} ({self.total_amount} {self.currency})>"
