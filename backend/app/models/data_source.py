from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    source_type = Column(String(30), nullable=False, index=True)  # BANK, PAYMENT_GATEWAY, ACCOUNTING, INVOICE, CRYPTO
    file_format = Column(String(10), nullable=False, default="CSV")  # CSV, JSON, XLSX
    account_identifier = Column(String(100), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    is_active = Column(Boolean, default=True)
    owner_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    transactions = relationship("Transaction", back_populates="source", cascade="all, delete-orphan")
    crypto_transactions = relationship("CryptoTransaction", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DataSource {self.name} ({self.source_type})>"
