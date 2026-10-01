from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchAlgorithmPass(str, Enum):
    PASS_1_EXACT = "PASS_1_EXACT"
    PASS_2_ID_CORRELATION = "PASS_2_ID_CORRELATION"
    PASS_3_FEE_NETTING = "PASS_3_FEE_NETTING"
    PASS_4_CRYPTO_ON_CHAIN = "PASS_4_CRYPTO_ON_CHAIN"
    PASS_5_FUZZY_ENTITY_AMOUNT = "PASS_5_FUZZY_ENTITY_AMOUNT"
    PASS_6_DUPLICATE_DETECTION = "PASS_6_DUPLICATE_DETECTION"
    PASS_7_ORPHAN_EXCEPTION = "PASS_7_ORPHAN_EXCEPTION"


class MatchStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    DUPLICATE = "DUPLICATE"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    MISSING_RECORD = "MISSING_RECORD"
    CONFLICTING_RECORD = "CONFLICTING_RECORD"
    UNMATCHED = "UNMATCHED"


class DiscrepancyType(str, Enum):
    AMOUNT = "AMOUNT"
    DATE = "DATE"
    ENTITY = "ENTITY"
    CURRENCY = "CURRENCY"
    STATUS = "STATUS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    MISSING_ENTRY = "MISSING_ENTRY"
    CONFLICTING_DATA = "CONFLICTING_DATA"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"      # Score >= 85.0
    MEDIUM = "MEDIUM"  # 65.0 <= Score < 85.0
    LOW = "LOW"        # Score < 65.0


class MatchEvidence(BaseModel):
    rule_name: str
    algorithm_pass: MatchAlgorithmPass
    score_contribution: float
    explanation: str
    details: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "algorithm_pass": self.algorithm_pass.value,
            "score_contribution": round(self.score_contribution, 2),
            "explanation": self.explanation,
            "details": self.details,
        }


class DiscrepancyDetail(BaseModel):
    discrepancy_type: DiscrepancyType
    field_name: str
    source_value: Optional[str] = None
    matched_value: Optional[str] = None
    difference_numeric: Optional[float] = None
    difference_percentage: Optional[float] = None
    root_cause_category: Optional[str] = None  # PROCESSING_FEE, T_PLUS_LAG, SLIPPAGE, DUPLICATE_ENTRY, UNRECORDED_EXPENSE
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "discrepancy_type": self.discrepancy_type.value,
            "field_name": self.field_name,
            "source_value": self.source_value,
            "matched_value": self.matched_value,
            "difference_numeric": round(self.difference_numeric, 4) if self.difference_numeric is not None else None,
            "difference_percentage": round(self.difference_percentage, 2) if self.difference_percentage is not None else None,
            "root_cause_category": self.root_cause_category,
            "severity": self.severity,
        }


class MatchCandidateResult(BaseModel):
    match_type: str  # TXN_TO_TXN, TXN_TO_INVOICE, CRYPTO_TO_INVOICE, CRYPTO_TO_ERP, DUPLICATE_PAIR
    match_status: MatchStatus
    confidence_score: float  # 0.0 - 100.0
    confidence_level: ConfidenceLevel
    algorithm_pass: MatchAlgorithmPass
    source_transaction_id: Optional[str] = None
    matched_transaction_id: Optional[str] = None
    crypto_transaction_id: Optional[str] = None
    invoice_id: Optional[str] = None
    evidence: List[MatchEvidence] = Field(default_factory=list)
    discrepancies: List[DiscrepancyDetail] = Field(default_factory=list)


class ReconciliationRunRequest(BaseModel):
    date_from: Optional[str] = Field(None, description="Optional start date ISO (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="Optional end date ISO (YYYY-MM-DD)")
    case_title: Optional[str] = Field(None, description="Descriptive title for this reconciliation run")
    amount_tolerance: float = Field(0.05, description="Allowed amount discrepancy tolerance in currency units")
    date_tolerance_days: int = Field(3, description="Allowed date lag window in days (T±3)")


class ReconciliationRunSummary(BaseModel):
    case_id: str
    case_number: str
    case_title: str
    total_records_processed: int
    exact_matches_count: int
    partial_matches_count: int
    discrepancies_count: int
    duplicates_count: int
    unmatched_count: int
    match_rate_percentage: float
    total_variance_amount: float
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_number": self.case_number,
            "case_title": self.case_title,
            "total_records_processed": self.total_records_processed,
            "exact_matches_count": self.exact_matches_count,
            "partial_matches_count": self.partial_matches_count,
            "discrepancies_count": self.discrepancies_count,
            "duplicates_count": self.duplicates_count,
            "unmatched_count": self.unmatched_count,
            "match_rate_percentage": round(self.match_rate_percentage, 2),
            "total_variance_amount": round(self.total_variance_amount, 2),
            "created_at": self.created_at,
        }
