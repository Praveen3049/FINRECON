from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.schemas.common import SourceType, BlockchainNetwork, MatchStatus, DiscrepancyType, ConfidenceLevel


class CanonicalTransactionBase(BaseModel):
    transaction_id: str
    source_type: SourceType
    source_name: str
    account_reference: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_id: Optional[str] = None
    amount: Decimal = Field(..., description="Normalized positive decimal value")
    currency: str = Field(default="USD", max_length=3)
    direction: str = Field(..., description="CREDIT or DEBIT")
    transaction_date: date
    transaction_timestamp: Optional[datetime] = None
    reference_number: Optional[str] = None
    invoice_id: Optional[str] = None
    payment_reference: Optional[str] = None
    description: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class CanonicalTransaction(CanonicalTransactionBase):
    id: str
    normalized_at: datetime
    created_at: datetime


class CanonicalInvoiceBase(BaseModel):
    invoice_number: str
    issuer_name: str
    recipient_name: str
    recipient_email: Optional[str] = None
    total_amount: Decimal
    currency: str = "USD"
    issue_date: date
    due_date: Optional[date] = None
    status: str = "ISSUED"  # ISSUED, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED
    reference_order_id: Optional[str] = None


class CanonicalInvoice(CanonicalInvoiceBase):
    id: str
    created_at: datetime


class CanonicalCryptoTransactionBase(BaseModel):
    transaction_hash: str
    blockchain_network: BlockchainNetwork
    wallet_from: str
    wallet_to: str
    asset: str = "USDT"  # USDT, USDC, ETH, BTC, etc.
    token_amount: Decimal
    fiat_value: Optional[Decimal] = None
    fiat_currency: str = "USD"
    transaction_timestamp: datetime
    block_number: Optional[int] = None
    gas_fee: Optional[Decimal] = None
    gas_fee_currency: Optional[str] = None
    confirmation_status: str = "CONFIRMED"
    associated_invoice_id: Optional[str] = None
    associated_reference: Optional[str] = None


class CanonicalCryptoTransaction(CanonicalCryptoTransactionBase):
    id: str
    created_at: datetime


class MatchEvidence(BaseModel):
    rule_applied: str
    entity_similarity_score: Optional[float] = None
    amount_difference: Optional[Decimal] = None
    amount_difference_percentage: Optional[float] = None
    date_difference_days: Optional[int] = None
    reference_match: bool = False
    hash_match: bool = False
    details: List[str] = []


class ReconciliationMatchResult(BaseModel):
    case_id: str
    primary_transaction_id: str
    matched_transaction_id: Optional[str] = None
    status: MatchStatus
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    confidence_level: ConfidenceLevel
    discrepancy_type: DiscrepancyType
    evidence: MatchEvidence
