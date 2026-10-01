from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReviewAction(str, Enum):
    CONFIRM_MATCH = "CONFIRM_MATCH"      # Approves match and resolves discrepancy
    REJECT_MATCH = "REJECT_MATCH"        # Unlinks match and flags records as unmatched
    MARK_DUPLICATE = "MARK_DUPLICATE"    # Suppresses duplicate and resolves discrepancy
    MARK_MISSING = "MARK_MISSING"        # Acknowledges missing entry and initiates ledger adjustment
    WRITE_OFF = "WRITE_OFF"              # Writes off small variance (fee/slippage)
    ESCALATE = "ESCALATE"                # Escalates to senior financial manager
    ASSIGN_AUDITOR = "ASSIGN_AUDITOR"    # Manager assigns case to designated auditor
    ADD_NOTE = "ADD_NOTE"                # Adds an audit commentary without status change


class ExceptionStatus(str, Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    WRITTEN_OFF = "WRITTEN_OFF"
    ESCALATED = "ESCALATED"


class ExceptionActionRequest(BaseModel):
    reviewer_name: str = Field(..., description="Name or role of financial operator")
    action: ReviewAction = Field(..., description="Action to execute")
    notes: Optional[str] = Field(None, description="Audit commentary or reasoning")
    adjustment_amount: Optional[float] = Field(None, description="Optional manual ledger adjustment amount")
    assigned_to: Optional[str] = Field(None, description="Designated auditor name if assigning case")


class BulkExceptionActionRequest(BaseModel):
    exception_ids: List[str] = Field(..., min_length=1, description="List of DiscrepancyRecord IDs")
    reviewer_name: str = Field(..., description="Name or role of financial operator")
    action: ReviewAction = Field(..., description="Action to apply across all selected exceptions")
    notes: Optional[str] = Field(None, description="Audit commentary")


class ExceptionSummaryResponse(BaseModel):
    total_open: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_variance_usd: float
    by_root_cause: Dict[str, int] = Field(default_factory=dict)
    by_discrepancy_type: Dict[str, int] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_open": self.total_open,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "total_variance_usd": round(self.total_variance_usd, 2),
            "by_root_cause": self.by_root_cause,
            "by_discrepancy_type": self.by_discrepancy_type,
        }
