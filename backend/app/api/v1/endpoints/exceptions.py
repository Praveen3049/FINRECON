from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import UserRole
from app.services.exceptions.models import (
    ExceptionActionRequest,
    BulkExceptionActionRequest,
)
from app.services.exceptions.service import ExceptionWorkbenchService

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def list_exceptions(
    status: Optional[str] = Query(None, description="OPEN, UNDER_REVIEW, RESOLVED, WRITTEN_OFF, ESCALATED"),
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    root_cause: Optional[str] = Query(None, description="PROCESSING_FEE, T_PLUS_LAG, SLIPPAGE, DUPLICATE_WEBHOOK, UNRECORDED_EXPENSE"),
    discrepancy_type: Optional[str] = Query(None, description="AMOUNT, DATE, DUPLICATE_ENTRY, MISSING_ENTRY"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Lists reconciliation exceptions and discrepancies with multi-attribute filtering.
    """
    return ExceptionWorkbenchService.get_exceptions(
        db=db,
        status=status,
        severity=severity,
        root_cause=root_cause,
        discrepancy_type=discrepancy_type,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=Dict[str, Any])
def get_exceptions_summary(
    db: Session = Depends(get_db),
):
    """
    Returns high-level exception metrics, severity breakdown, and root cause distributions.
    """
    return ExceptionWorkbenchService.get_summary(db=db)


@router.get("/{exception_id}", response_model=Dict[str, Any])
def get_exception_detail(
    exception_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves full exception history, prior reviewer actions, and audit trail.
    """
    detail = ExceptionWorkbenchService.get_exception_detail(db=db, exception_id=exception_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception '{exception_id}' not found.",
        )
    return detail


@router.post("/{exception_id}/action", response_model=Dict[str, Any])
def apply_exception_action(
    exception_id: str,
    req: ExceptionActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    _user=Depends(require_role(UserRole.AUDITOR, UserRole.MANAGER)),
):
    """
    Applies an operator action (CONFIRM_MATCH, REJECT_MATCH, WRITE_OFF, ESCALATE, MARK_DUPLICATE, ASSIGN_AUDITOR).
    Emits an immutable entry to AuditLog.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    res = ExceptionWorkbenchService.execute_action(
        db=db,
        exception_id=exception_id,
        reviewer_name=req.reviewer_name,
        action=req.action.value,
        notes=req.notes,
        adjustment_amount=req.adjustment_amount,
        ip_address=client_ip,
        assigned_to=req.assigned_to,
    )
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception '{exception_id}' not found.",
        )
    return res


@router.post("/bulk-action", response_model=Dict[str, Any])
def apply_bulk_exception_actions(
    req: BulkExceptionActionRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_role(UserRole.AUDITOR, UserRole.MANAGER)),
):
    """
    Applies a review action across multiple exceptions simultaneously.
    """
    return ExceptionWorkbenchService.execute_bulk_actions(
        db=db,
        exception_ids=req.exception_ids,
        reviewer_name=req.reviewer_name,
        action=req.action.value,
        notes=req.notes,
    )
