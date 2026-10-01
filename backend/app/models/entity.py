from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, index=True)
    legal_name = Column(String(200), nullable=True)
    entity_type = Column(String(30), nullable=False, default="CUSTOMER")  # CUSTOMER, VENDOR, PARTNER, INTERNAL
    tax_id = Column(String(50), nullable=True, index=True)
    email = Column(String(100), nullable=True, index=True)
    phone = Column(String(30), nullable=True)
    wallet_address = Column(String(100), nullable=True, index=True)
    bank_account_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    transactions = relationship("Transaction", back_populates="entity")
    invoices = relationship("Invoice", back_populates="entity")

    def __repr__(self):
        return f"<Entity {self.name} ({self.entity_type})>"
