from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditLogFilter(BaseModel):
    actor_type: Optional[str] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    case_id: Optional[str] = None
    query: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=50000)
    offset: int = Field(default=0, ge=0)


class AuditLogItemResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    case_id: Optional[str] = None
    actor_type: str
    actor_id: str
    action: str
    old_state: Optional[Any] = None
    new_state: Optional[Any] = None
    details: str
    ip_address: Optional[str] = None
    timestamp: str
    entry_hash: Optional[str] = None
    prev_hash: Optional[str] = None
    is_tamper_verified: bool = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChainVerificationResponse(BaseModel):
    is_valid: bool
    total_blocks: int
    verified_blocks: int
    genesis_block_id: Optional[str] = None
    genesis_hash: Optional[str] = None
    latest_block_id: Optional[str] = None
    latest_hash: Optional[str] = None
    broken_blocks: List[Dict[str, Any]] = []
    message: str
    verified_at: str


class AuditSummaryResponse(BaseModel):
    total_events: int
    automated_events: int
    manual_events: int
    ai_events: int
    automation_percentage: float
    chain_status: str  # HEALTHY, TAMPER_DETECTED, EMPTY
    verified_blocks_count: int
    genesis_hash: Optional[str] = None
    latest_hash: Optional[str] = None
    actor_breakdown: Dict[str, int]
    action_breakdown: Dict[str, int]
    entity_breakdown: Dict[str, int]
    compliance_controls: Dict[str, Any]


class CompliancePackageResponse(BaseModel):
    report_id: str
    title: str
    standard: str
    organization: str
    generated_at: str
    summary: AuditSummaryResponse
    chain_verification: ChainVerificationResponse
    event_logs: List[AuditLogItemResponse]
