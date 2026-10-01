from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_role
from app.models.user import UserRole
from app.services.reconciliation.models import (
    ReconciliationRunRequest,
    ReconciliationRunSummary,
)
from app.services.reconciliation.service import ReconciliationService

router = APIRouter()


class ReviewSubmissionRequest(BaseModel):
    reviewer_name: str = Field(..., description="Name or ID of reviewer")
    action: str = Field(..., description="CONFIRM_MATCH, REJECT_MATCH, MARK_DUPLICATE, ESCALATE, ADD_NOTE")
    notes: Optional[str] = None


@router.post("/run", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def trigger_reconciliation_run(
    req: ReconciliationRunRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_role(UserRole.AUDITOR, UserRole.MANAGER)),
):
    """
    Triggers an end-to-end multi-pass reconciliation run across Bank, Gateway,
    ERP/Accounting, Invoices, and Crypto feeds.
    Produces a persisted ReconciliationCase with matches, confidence levels, and discrepancies.
    """
    summary = ReconciliationService.execute_reconciliation(db=db, req=req)
    return summary.to_dict()


@router.get("/cases", response_model=List[Dict[str, Any]])
def list_reconciliation_cases(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retrieves all reconciliation runs/cases with status and summary metrics.
    """
    return ReconciliationService.get_cases(db=db, limit=limit, offset=offset)


@router.get("/cases/{case_id}", response_model=Dict[str, Any])
def get_reconciliation_case(
    case_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves detailed breakdown of a reconciliation case including matches,
    source-to-target links, explainable evidence, and discrepancies.
    """
    case_data = ReconciliationService.get_case_detail(db=db, case_id=case_id)
    if not case_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation case '{case_id}' not found.",
        )
    return case_data


@router.get("/matches", response_model=List[Dict[str, Any]])
def list_matches(
    case_id: Optional[str] = None,
    match_status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Lists reconciliation matches with optional filtering by case_id or match_status.
    """
    return ReconciliationService.get_all_matches(
        db=db, case_id=case_id, status=match_status, limit=limit, offset=offset
    )


@router.post("/matches/{match_id}/review", response_model=Dict[str, Any])
def review_match(
    match_id: str,
    req: ReviewSubmissionRequest,
    db: Session = Depends(get_db),
):
    """
    Submits a manual review action for an exception, partial match, or ambiguous record.
    """
    review = ReconciliationService.submit_review(
        db=db,
        match_id=match_id,
        reviewer_name=req.reviewer_name,
        action=req.action,
        notes=req.notes,
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match '{match_id}' not found.",
        )

    return {
        "message": f"Review action '{req.action}' submitted successfully.",
        "review_id": review.id,
        "match_id": review.match_id,
        "previous_status": review.previous_status,
        "new_status": review.new_status,
        "reviewer": review.reviewer_name,
        "created_at": review.created_at.isoformat(),
    }
