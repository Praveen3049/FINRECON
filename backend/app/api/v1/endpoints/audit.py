from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.audit.models import (
    AuditLogFilter,
    AuditLogItemResponse,
    AuditLogListResponse,
    AuditSummaryResponse,
    ChainVerificationResponse,
    CompliancePackageResponse,
)
from app.services.audit.service import AuditService

router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
def list_audit_logs(
    actor_type: Optional[str] = Query(None, description="SYSTEM_ENGINE, MANUAL_REVIEWER, AI_ASSISTANT"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID/name"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    entity_type: Optional[str] = Query(None, description="TRANSACTION, CASE, MATCH, DISCREPANCY, INVOICE, CRYPTO"),
    entity_id: Optional[str] = Query(None, description="Filter by specific entity ID"),
    case_id: Optional[str] = Query(None, description="Filter by reconciliation case ID"),
    query: Optional[str] = Query(None, description="Free text search over details, actors, actions"),
    start_date: Optional[str] = Query(None, description="ISO start timestamp"),
    end_date: Optional[str] = Query(None, description="ISO end timestamp"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Query paginated, filterable, and searchable immutable audit logs.
    """
    filters = AuditLogFilter(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        case_id=case_id,
        query=query,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return AuditService.get_audit_logs(db, filters)


@router.get("/summary", response_model=AuditSummaryResponse)
def get_audit_summary(db: Session = Depends(get_db)):
    """
    Retrieve executive compliance overview, automation metrics, and cryptographic integrity state.
    """
    return AuditService.get_audit_summary(db)


@router.post("/verify-integrity", response_model=ChainVerificationResponse)
def verify_audit_integrity(db: Session = Depends(get_db)):
    """
    Cryptographically verify the entire SHA-256 hash chain across all audit logs.
    """
    return AuditService.verify_chain_integrity(db)


@router.get("/logs/{log_id}", response_model=AuditLogItemResponse)
def get_audit_log_detail(log_id: str, db: Session = Depends(get_db)):
    """
    Retrieve single audit record with state diff, actor metadata, and cryptographic hash signature.
    """
    log_item = AuditService.get_audit_log_by_id(db, log_id)
    if not log_item:
        raise HTTPException(status_code=404, detail=f"Audit log with ID {log_id} not found")
    return log_item


@router.get("/export/csv")
def export_audit_csv(
    actor_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Download complete audit log history as an RFC 4180 compliant CSV spreadsheet.
    """
    filters = AuditLogFilter(
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        query=query,
        limit=10000,
        offset=0,
    )
    csv_data = AuditService.export_csv(db, filters)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=finrecon_audit_trail_export.csv"
        },
    )


@router.get("/export/compliance-package", response_model=CompliancePackageResponse)
def export_compliance_package(db: Session = Depends(get_db)):
    """
    Generate an auditor-ready SOX-404 & SOC 2 Type II compliance package with cryptographic proof.
    """
    return AuditService.export_compliance_package(db)
