from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(30), nullable=False, index=True)  # BANK, PAYMENT_GATEWAY, ACCOUNTING, INVOICE, CRYPTO
    external_transaction_id = Column(String(100), nullable=False, index=True)
    
    entity_id = Column(String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True)
    counterparty_raw_name = Column(String(150), nullable=True)
    counterparty_normalized_name = Column(String(150), nullable=True, index=True)
    
    amount = Column(Numeric(18, 4), nullable=False, index=True)
    fee_amount = Column(Numeric(18, 4), nullable=True, default=0.0)
    net_amount = Column(Numeric(18, 4), nullable=True, index=True)
    currency = Column(String(3), nullable=False, default="USD", index=True)
    direction = Column(String(10), nullable=False, index=True)  # CREDIT, DEBIT
    
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_timestamp = Column(DateTime, nullable=True, index=True)
    
    reference_number = Column(String(100), nullable=True, index=True)
    invoice_reference = Column(String(100), nullable=True, index=True)
    payment_reference = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON-encoded raw string
    status = Column(String(30), nullable=False, default="SETTLED", index=True)  # PENDING, SETTLED, FAILED, REVERSED
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    source = relationship("DataSource", back_populates="transactions")
    entity = relationship("Entity", back_populates="transactions")

    __table_args__ = (
        Index("idx_txn_source_date", "source_type", "transaction_date"),
        Index("idx_txn_amount_currency", "amount", "currency"),
        Index("idx_txn_ref_date", "reference_number", "transaction_date"),
    )

    def __repr__(self):
        return f"<Transaction {self.external_transaction_id} ({self.source_type}: {self.amount} {self.currency})>"
