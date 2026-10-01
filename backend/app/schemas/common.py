from enum import Enum
from typing import Generic, Optional, TypeVar, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceType(str, Enum):
    BANK = "BANK"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    ACCOUNTING = "ACCOUNTING"
    INVOICE = "INVOICE"
    CRYPTO = "CRYPTO"


class MatchStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    DUPLICATE = "DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    MISSING_RECORD = "MISSING_RECORD"
    CONFLICTING_RECORD = "CONFLICTING_RECORD"
    UNMATCHED = "UNMATCHED"


class DiscrepancyType(str, Enum):
    NONE = "NONE"
    AMOUNT = "AMOUNT"
    DATE = "DATE"
    ENTITY = "ENTITY"
    CURRENCY = "CURRENCY"
    STATUS = "STATUS"
    MULTI_FIELD = "MULTI_FIELD"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RECONCILED = "RECONCILED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class BlockchainNetwork(str, Enum):
    ETHEREUM = "ETHEREUM"
    POLYGON = "POLYGON"
    BITCOIN = "BITCOIN"
    SOLANA = "SOLANA"
    ARBITRUM = "ARBITRUM"


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None
    errors: Optional[List[str]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
