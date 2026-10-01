from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.reconciliation_case import ReconciliationCase
from app.models.reconciliation_match import ReconciliationMatch
from app.models.discrepancy_record import DiscrepancyRecord
from app.models.manual_review import ManualReview
from app.models.transaction import Transaction
from app.models.invoice import Invoice
from app.models.crypto_transaction import CryptoTransaction

from app.services.reconciliation.models import (
    ReconciliationRunRequest,
    ReconciliationRunSummary,
    MatchStatus,
)
from app.services.reconciliation.engine import ReconciliationEngine


class ReconciliationService:
    """
    Coordinates reconciliation runs, database persistence of cases, matches,
    discrepancies, and manual reviews.
    """

    @classmethod
    def execute_reconciliation(
        cls,
        db: Session,
        req: ReconciliationRunRequest,
    ) -> ReconciliationRunSummary:
        # 1. Fetch transactions, invoices, crypto transactions
        txn_query = db.query(Transaction)
        inv_query = db.query(Invoice)
        crypto_query = db.query(CryptoTransaction)

        if req.date_from:
            d_from = datetime.strptime(req.date_from, "%Y-%m-%d").date()
            txn_query = txn_query.filter(Transaction.transaction_date >= d_from)
            inv_query = inv_query.filter(Invoice.issue_date >= d_from)
            crypto_query = crypto_query.filter(CryptoTransaction.transaction_timestamp >= datetime.combine(d_from, datetime.min.time()))

        if req.date_to:
            d_to = datetime.strptime(req.date_to, "%Y-%m-%d").date()
            txn_query = txn_query.filter(Transaction.transaction_date <= d_to)
            inv_query = inv_query.filter(Invoice.issue_date <= d_to)
            crypto_query = crypto_query.filter(CryptoTransaction.transaction_timestamp <= datetime.combine(d_to, datetime.max.time()))

        transactions = txn_query.all()
        invoices = inv_query.all()
        crypto_transactions = crypto_query.all()

        total_records = len(transactions) + len(invoices) + len(crypto_transactions)

        # 2. Create Reconciliation Case
        now = datetime.now(timezone.utc)
        case_num = f"CASE-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
        case_title = req.case_title or f"Multi-Feed Reconciliation Run {case_num}"

        recon_case = ReconciliationCase(
            id=str(uuid.uuid4()),
            case_number=case_num,
            title=case_title,
            status="UNDER_REVIEW",
            priority="HIGH",
            primary_source_type="MULTI_FEED",
            total_variance_amount=Decimal("0.0"),
            total_date_variance_days=0,
            created_at=now,
        )
        db.add(recon_case)
        db.flush()

        # 3. Execute Multi-Pass Reconciliation Engine
        match_results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=transactions,
            invoices=invoices,
            crypto_transactions=crypto_transactions,
            date_tolerance_days=req.date_tolerance_days,
            amount_tolerance=req.amount_tolerance,
        )

        exact_count = 0
        partial_count = 0
        dup_count = 0
        discrepancy_count = 0
        unmatched_count = 0
        total_variance = Decimal("0.0")

        # 4. Persist matches and discrepancies
        for mr in match_results:
            match_orm = ReconciliationMatch(
                id=str(uuid.uuid4()),
                case_id=recon_case.id,
                source_transaction_id=mr.source_transaction_id,
                matched_transaction_id=mr.matched_transaction_id,
                crypto_transaction_id=mr.crypto_transaction_id,
                invoice_id=mr.invoice_id,
                match_type=mr.match_type,
                match_status=mr.match_status.value,
                confidence_score=mr.confidence_score,
                confidence_level=mr.confidence_level.value,
                algorithm_pass=mr.algorithm_pass.value,
                evidence_json=json.dumps([e.to_dict() for e in mr.evidence]),
                created_at=now,
            )
            db.add(match_orm)
            db.flush()

            if mr.match_status == MatchStatus.EXACT_MATCH:
                exact_count += 1
            elif mr.match_status == MatchStatus.PARTIAL_MATCH:
                partial_count += 1
            elif mr.match_status == MatchStatus.DUPLICATE:
                dup_count += 1
            elif mr.match_status == MatchStatus.MISSING_RECORD:
                unmatched_count += 1

            # Persist Discrepancies
            for disc in mr.discrepancies:
                discrepancy_count += 1
                diff_dec = Decimal(str(disc.difference_numeric)) if disc.difference_numeric is not None else Decimal("0.0")
                if diff_dec == Decimal("0.0") and mr.source_transaction_id:
                    src_t = next((t for t in transactions if t.id == mr.source_transaction_id), None)
                    if src_t and getattr(src_t, "amount", None):
                        diff_dec = Decimal(str(src_t.amount))

                if disc.discrepancy_type.value == "AMOUNT":
                    total_variance += abs(diff_dec)

                disc_orm = DiscrepancyRecord(
                    id=str(uuid.uuid4()),
                    case_id=recon_case.id,
                    match_id=match_orm.id,
                    discrepancy_type=disc.discrepancy_type.value,
                    field_name=disc.field_name,
                    source_value=disc.source_value,
                    matched_value=disc.matched_value,
                    difference_numeric=diff_dec,
                    difference_percentage=disc.difference_percentage,
                    root_cause_category=disc.root_cause_category,
                    severity=disc.severity,
                    created_at=now,
                )
                db.add(disc_orm)

        recon_case.total_variance_amount = total_variance
        recon_case.status = "RECONCILED" if (partial_count == 0 and dup_count == 0 and unmatched_count == 0) else "UNDER_REVIEW"
        db.commit()

        matched_records_total = exact_count + partial_count
        match_rate = (matched_records_total / max(1, total_records)) * 100.0 if total_records > 0 else 100.0

        return ReconciliationRunSummary(
            case_id=recon_case.id,
            case_number=recon_case.case_number,
            case_title=recon_case.title,
            total_records_processed=total_records,
            exact_matches_count=exact_count,
            partial_matches_count=partial_count,
            discrepancies_count=discrepancy_count,
            duplicates_count=dup_count,
            unmatched_count=unmatched_count,
            match_rate_percentage=min(100.0, match_rate),
            total_variance_amount=float(total_variance),
            created_at=recon_case.created_at.isoformat(),
        )

    @classmethod
    def get_cases(cls, db: Session, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        cases = db.query(ReconciliationCase).order_by(ReconciliationCase.created_at.desc()).offset(offset).limit(limit).all()
        results = []
        for c in cases:
            m_count = db.query(func.count(ReconciliationMatch.id)).filter(ReconciliationMatch.case_id == c.id).scalar() or 0
            d_count = db.query(func.count(DiscrepancyRecord.id)).filter(DiscrepancyRecord.case_id == c.id).scalar() or 0

            results.append({
                "id": c.id,
                "case_number": c.case_number,
                "title": c.title,
                "status": c.status,
                "priority": c.priority,
                "primary_source_type": c.primary_source_type,
                "total_variance_amount": float(c.total_variance_amount or 0.0),
                "matches_count": m_count,
                "discrepancies_count": d_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return results

    @classmethod
    def get_case_detail(cls, db: Session, case_id: str) -> Optional[Dict[str, Any]]:
        c = db.query(ReconciliationCase).filter(ReconciliationCase.id == case_id).first()
        if not c:
            return None

        matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.case_id == c.id).all()
        discrepancies = db.query(DiscrepancyRecord).filter(DiscrepancyRecord.case_id == c.id).all()

        formatted_matches = []
        for m in matches:
            evidence_data = []
            if m.evidence_json:
                try:
                    evidence_data = json.loads(m.evidence_json)
                except Exception:
                    pass

            src_txn = db.query(Transaction).filter(Transaction.id == m.source_transaction_id).first() if m.source_transaction_id else None
            tgt_txn = db.query(Transaction).filter(Transaction.id == m.matched_transaction_id).first() if m.matched_transaction_id else None
            inv = db.query(Invoice).filter(Invoice.id == m.invoice_id).first() if m.invoice_id else None
            crypto = db.query(CryptoTransaction).filter(CryptoTransaction.id == m.crypto_transaction_id).first() if m.crypto_transaction_id else None

            formatted_matches.append({
                "id": m.id,
                "match_type": m.match_type,
                "match_status": m.match_status,
                "confidence_score": m.confidence_score,
                "confidence_level": m.confidence_level,
                "algorithm_pass": m.algorithm_pass,
                "evidence": evidence_data,
                "source": {
                    "id": src_txn.id,
                    "transaction_id": getattr(src_txn, "external_transaction_id", getattr(src_txn, "transaction_id", src_txn.id)),
                    "amount": float(src_txn.amount),
                    "currency": src_txn.currency,
                    "source_type": src_txn.source_type,
                    "date": src_txn.transaction_date.isoformat() if src_txn.transaction_date else None,
                    "reference": src_txn.payment_reference,
                } if src_txn else None,
                "target": {
                    "id": tgt_txn.id if tgt_txn else (inv.id if inv else (crypto.id if crypto else None)),
                    "identifier": (
                        getattr(tgt_txn, "external_transaction_id", getattr(tgt_txn, "transaction_id", tgt_txn.id))
                        if tgt_txn
                        else (inv.invoice_number if inv else getattr(crypto, "transaction_hash", getattr(crypto, "tx_hash", "CRYPTO")))
                    ),
                    "amount": float(tgt_txn.amount) if tgt_txn else (float(inv.total_amount) if inv else float(getattr(crypto, "fiat_value", None) or getattr(crypto, "amount_usd", None) or crypto.token_amount or crypto.amount or 0.0)),
                    "currency": tgt_txn.currency if tgt_txn else (inv.currency if inv else getattr(crypto, "asset", getattr(crypto, "token_symbol", "USDT"))),
                    "type": "TRANSACTION" if tgt_txn else ("INVOICE" if inv else "CRYPTO"),
                } if (tgt_txn or inv or crypto) else None,
            })

        return {
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "status": c.status,
            "priority": c.priority,
            "total_variance_amount": float(c.total_variance_amount or 0.0),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "matches": formatted_matches,
            "discrepancies": [
                {
                    "id": d.id,
                    "match_id": d.match_id,
                    "discrepancy_type": d.discrepancy_type,
                    "field_name": d.field_name,
                    "source_value": d.source_value,
                    "matched_value": d.matched_value,
                    "difference_numeric": float(d.difference_numeric or 0.0),
                    "difference_percentage": d.difference_percentage,
                    "root_cause_category": d.root_cause_category,
                    "severity": d.severity,
                }
                for d in discrepancies
            ],
        }

    @classmethod
    def get_all_matches(
        cls,
        db: Session,
        case_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        q = db.query(ReconciliationMatch)
        if case_id:
            q = q.filter(ReconciliationMatch.case_id == case_id)
        if status:
            q = q.filter(ReconciliationMatch.match_status == status)

        matches = q.order_by(ReconciliationMatch.created_at.desc()).offset(offset).limit(limit).all()
        results = []
        for m in matches:
            evidence_data = []
            if m.evidence_json:
                try:
                    evidence_data = json.loads(m.evidence_json)
                except Exception:
                    pass

            results.append({
                "id": m.id,
                "case_id": m.case_id,
                "match_type": m.match_type,
                "match_status": m.match_status,
                "confidence_score": m.confidence_score,
                "confidence_level": m.confidence_level,
                "algorithm_pass": m.algorithm_pass,
                "evidence": evidence_data,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        return results

    @classmethod
    def submit_review(
        cls,
        db: Session,
        match_id: str,
        reviewer_name: str,
        action: str,
        notes: Optional[str] = None,
    ) -> Optional[ManualReview]:
        match = db.query(ReconciliationMatch).filter(ReconciliationMatch.id == match_id).first()
        if not match:
            return None

        prev_status = match.match_status
        new_status = prev_status

        if action == "CONFIRM_MATCH":
            new_status = "EXACT_MATCH"
        elif action == "REJECT_MATCH":
            new_status = "UNMATCHED"
        elif action == "MARK_DUPLICATE":
            new_status = "DUPLICATE"

        match.match_status = new_status

        review = ManualReview(
            id=str(uuid.uuid4()),
            case_id=match.case_id,
            match_id=match.id,
            reviewer_name=reviewer_name,
            action=action,
            previous_status=prev_status,
            new_status=new_status,
            notes=notes,
            created_at=datetime.now(timezone.utc),
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
