from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Numeric, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class CryptoTransaction(Base):
    __tablename__ = "crypto_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=True, index=True)
    
    transaction_hash = Column(String(100), unique=True, nullable=False, index=True)
    blockchain_network = Column(String(30), nullable=False, index=True)  # ETHEREUM, POLYGON, BITCOIN, SOLANA, ARBITRUM
    wallet_from = Column(String(100), nullable=False, index=True)
    wallet_to = Column(String(100), nullable=False, index=True)
    
    asset = Column(String(20), nullable=False, default="USDT", index=True)  # USDT, USDC, ETH, BTC, MATIC
    token_amount = Column(Numeric(28, 8), nullable=False, index=True)
    fiat_value = Column(Numeric(18, 4), nullable=True, index=True)
    fiat_currency = Column(String(3), nullable=False, default="USD")
    
    transaction_timestamp = Column(DateTime, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=True)
    gas_fee = Column(Numeric(28, 8), nullable=True)
    gas_fee_fiat = Column(Numeric(18, 4), nullable=True)
    confirmation_status = Column(String(30), nullable=False, default="CONFIRMED", index=True)  # CONFIRMED, PENDING, DROPPED
    
    associated_invoice_id = Column(String(100), nullable=True, index=True)
    associated_reference = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    source = relationship("DataSource", back_populates="crypto_transactions")

    __table_args__ = (
        Index("idx_crypto_network_timestamp", "blockchain_network", "transaction_timestamp"),
        Index("idx_crypto_wallet_to_asset", "wallet_to", "asset"),
        Index("idx_crypto_fiat_value", "fiat_value", "fiat_currency"),
    )

    def __repr__(self):
        return f"<CryptoTransaction {self.transaction_hash[:10]}... ({self.token_amount} {self.asset} ~ ${self.fiat_value})>"
