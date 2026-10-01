from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("reconciliation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    matched_transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    crypto_transaction_id = Column(String(36), ForeignKey("crypto_transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    match_type = Column(String(50), nullable=False)  # TXN_TO_TXN, TXN_TO_INVOICE, CRYPTO_TO_INVOICE, CRYPTO_TO_ERP, DUPLICATE_PAIR
    match_status = Column(String(30), nullable=False, index=True)  # EXACT_MATCH, PARTIAL_MATCH, DUPLICATE, POSSIBLE_DUPLICATE, MISSING_RECORD, CONFLICTING_RECORD, UNMATCHED
    confidence_score = Column(Float, nullable=False, index=True)  # 0.0 - 100.0
    confidence_level = Column(String(10), nullable=False, index=True)  # HIGH, MEDIUM, LOW
    
    algorithm_pass = Column(String(50), nullable=False)  # PASS_1_EXACT, PASS_2_ID_CORRELATION, PASS_3_RAPIDFUZZ, PASS_4_CRYPTO_MATCH, PASS_5_ANOMALY
    evidence_json = Column(Text, nullable=True)  # JSON-encoded explanation evidence
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    case = relationship("ReconciliationCase", back_populates="matches")
    source_transaction = relationship("Transaction", foreign_keys=[source_transaction_id])
    matched_transaction = relationship("Transaction", foreign_keys=[matched_transaction_id])
    crypto_transaction = relationship("CryptoTransaction", foreign_keys=[crypto_transaction_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    discrepancies = relationship("DiscrepancyRecord", back_populates="match", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_match_status_confidence", "match_status", "confidence_score"),
        Index("idx_match_algorithm_pass", "algorithm_pass", "confidence_level"),
    )

    def __repr__(self):
        return f"<ReconciliationMatch {self.match_status} (Score: {self.confidence_score}% via {self.algorithm_pass})>"
