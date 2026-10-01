from typing import Dict, Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models import (
    DataSource,
    Entity,
    Transaction,
    Invoice,
    CryptoTransaction,
    ReconciliationCase,
    ReconciliationMatch,
    DiscrepancyRecord,
    ManualReview,
    AuditLog,
)
from app.utils.seed_data import seed_database

router = APIRouter()


@router.get("/database-summary", status_code=status.HTTP_200_OK, tags=["Database"])
def get_database_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns a full summary of records across all 10 FinRecon tables."""
    counts = {
        "data_sources": db.query(DataSource).count(),
        "entities": db.query(Entity).count(),
        "transactions": db.query(Transaction).count(),
        "invoices": db.query(Invoice).count(),
        "crypto_transactions": db.query(CryptoTransaction).count(),
        "reconciliation_cases": db.query(ReconciliationCase).count(),
        "reconciliation_matches": db.query(ReconciliationMatch).count(),
        "discrepancy_records": db.query(DiscrepancyRecord).count(),
        "manual_reviews": db.query(ManualReview).count(),
        "audit_logs": db.query(AuditLog).count(),
    }

    # Matches breakdown by status
    matches_by_status = dict(
        db.query(ReconciliationMatch.match_status, func.count(ReconciliationMatch.id))
        .group_by(ReconciliationMatch.match_status)
        .all()
    )

    # Discrepancies by type
    discrepancies_by_type = dict(
        db.query(DiscrepancyRecord.discrepancy_type, func.count(DiscrepancyRecord.id))
        .group_by(DiscrepancyRecord.discrepancy_type)
        .all()
    )

    # Transactions by source type
    txns_by_source = dict(
        db.query(Transaction.source_type, func.count(Transaction.id))
        .group_by(Transaction.source_type)
        .all()
    )

    # Cases breakdown by status
    cases_by_status = dict(
        db.query(ReconciliationCase.status, func.count(ReconciliationCase.id))
        .group_by(ReconciliationCase.status)
        .all()
    )

    # Discrepancies by status
    discrepancies_by_status = dict(
        db.query(DiscrepancyRecord.status, func.count(DiscrepancyRecord.id))
        .group_by(DiscrepancyRecord.status)
        .all()
    )

    # Recent cases
    cases = db.query(ReconciliationCase).order_by(ReconciliationCase.created_at.desc()).limit(10).all()
    case_list = [
        {
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "status": c.status,
            "priority": c.priority,
            "primary_source_type": c.primary_source_type,
            "variance_amount": float(c.total_variance_amount or 0.0),
            "date_variance_days": c.total_date_variance_days,
            "matches_count": len(c.matches),
            "discrepancies_count": len(c.discrepancies),
        }
        for c in cases
    ]

    return {
        "status": "success",
        "total_tables": 10,
        "table_counts": counts,
        "case_distribution": cases_by_status,
        "match_distribution": matches_by_status,
        "discrepancy_distribution": discrepancies_by_type,
        "discrepancy_status_distribution": discrepancies_by_status,
        "transactions_by_source": txns_by_source,
        "recent_cases": case_list,
    }


@router.post("/seed", status_code=status.HTTP_201_CREATED, tags=["Database"])
async def trigger_seed(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Populates database with official Aczen Nova accounting records."""
    from app.core.config import settings
    if settings.NOVA_API_KEY:
        from app.services.ingestion.aczen_sync import AczenNovaSyncService
        res = await AczenNovaSyncService.sync_and_replace_with_aczen_data(db, purge_old_data=True)
        return res
    summary = seed_database(db)
    return {
        "status": "success",
        "message": "Database populated with fallback records",
        "counts": summary,
    }
