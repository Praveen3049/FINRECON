from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import json
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.discrepancy_record import DiscrepancyRecord
from app.models.reconciliation_match import ReconciliationMatch
from app.models.reconciliation_case import ReconciliationCase
from app.models.manual_review import ManualReview
from app.models.audit_log import AuditLog
from app.models.transaction import Transaction
from app.models.invoice import Invoice
from app.models.crypto_transaction import CryptoTransaction
from app.services.audit.service import AuditService
from app.services.exceptions.models import (
    ExceptionSummaryResponse,
    ReviewAction,
)


class ExceptionWorkbenchService:
    """
    Manages exception workflows, manual reviewer decisions,
    audit trails, and ledger adjustment notes.
    """

    @classmethod
    def get_exceptions(
        cls,
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        root_cause: Optional[str] = None,
        discrepancy_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        q = db.query(DiscrepancyRecord)

        if status:
            q = q.filter(DiscrepancyRecord.status == status.upper())
        if severity:
            q = q.filter(DiscrepancyRecord.severity == severity.upper())
        if root_cause:
            q = q.filter(DiscrepancyRecord.root_cause_category == root_cause.upper())
        if discrepancy_type:
            q = q.filter(DiscrepancyRecord.discrepancy_type == discrepancy_type.upper())

        from sqlalchemy import case
        severity_order = case(
            (DiscrepancyRecord.severity == "CRITICAL", 1),
            (DiscrepancyRecord.severity == "HIGH", 2),
            (DiscrepancyRecord.severity == "MEDIUM", 3),
            else_=4,
        )
        type_order = case(
            (DiscrepancyRecord.discrepancy_type == "AMOUNT", 1),
            (DiscrepancyRecord.discrepancy_type == "MISSING_ENTRY", 2),
            (DiscrepancyRecord.discrepancy_type == "DATE", 3),
            else_=4,
        )

        discrepancies = (
            q.order_by(
                severity_order,
                type_order,
                DiscrepancyRecord.difference_numeric.desc(),
                DiscrepancyRecord.created_at.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
        results = []

        # Batch-prefetch related records to eliminate N+1 queries
        match_ids = [d.match_id for d in discrepancies if d.match_id]
        matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.id.in_(match_ids)).all() if match_ids else []
        matches_by_id = {m.id: m for m in matches}

        src_txn_ids = [m.source_transaction_id for m in matches if m.source_transaction_id]
        tgt_txn_ids = [m.matched_transaction_id for m in matches if m.matched_transaction_id]
        all_txn_ids = list(set(src_txn_ids + tgt_txn_ids))
        txns = db.query(Transaction).filter(Transaction.id.in_(all_txn_ids)).all() if all_txn_ids else []
        txns_by_id = {t.id: t for t in txns}

        inv_ids = [m.invoice_id for m in matches if m.invoice_id]
        invoices = db.query(Invoice).filter(Invoice.id.in_(inv_ids)).all() if inv_ids else []
        invoices_by_id = {i.id: i for i in invoices}

        crypto_ids = [m.crypto_transaction_id for m in matches if m.crypto_transaction_id]
        cryptos = db.query(CryptoTransaction).filter(CryptoTransaction.id.in_(crypto_ids)).all() if crypto_ids else []
        cryptos_by_id = {c.id: c for c in cryptos}

        for d in discrepancies:
            match = matches_by_id.get(d.match_id) if d.match_id else None
            
            src_txn = txns_by_id.get(match.source_transaction_id) if match and match.source_transaction_id else None
            tgt_txn = txns_by_id.get(match.matched_transaction_id) if match and match.matched_transaction_id else None
            inv = invoices_by_id.get(match.invoice_id) if match and match.invoice_id else None
            crypto = cryptos_by_id.get(match.crypto_transaction_id) if match and match.crypto_transaction_id else None

            # Determine whether matched target is Invoice, Crypto, or Transaction
            use_inv = (inv is not None) and (
                match and match.match_type == "TXN_TO_INVOICE"
                or d.field_name == "total_amount"
                or tgt_txn is None
            )

            # Resolve Source A amount accurately
            src_amount = 0.0
            if d.discrepancy_type == "AMOUNT" and d.source_value:
                try:
                    src_amount = float(d.source_value)
                except (ValueError, TypeError):
                    src_amount = float(src_txn.amount) if src_txn else 0.0
            elif src_txn:
                src_amount = float(src_txn.amount)
            elif d.source_value:
                try:
                    src_amount = float(d.source_value)
                except (ValueError, TypeError):
                    src_amount = 0.0

            # Resolve Source B amount & details
            matched_id = None
            matched_identifier = None
            matched_amount = 0.0
            matched_type = "NONE"
            matched_entity = None
            matched_date = None

            if use_inv and inv:
                matched_id = inv.id
                matched_identifier = inv.invoice_number
                matched_type = "INVOICE"
                matched_entity = inv.recipient_name or inv.issuer_name
                matched_date = inv.issue_date.isoformat() if inv.issue_date else None
                if d.discrepancy_type == "AMOUNT" and d.matched_value:
                    try:
                        matched_amount = float(d.matched_value)
                    except (ValueError, TypeError):
                        matched_amount = float(inv.total_amount)
                else:
                    matched_amount = float(inv.total_amount)
            elif crypto:
                matched_id = crypto.id
                matched_identifier = getattr(crypto, "transaction_hash", "CRYPTO")
                matched_amount = float(getattr(crypto, "fiat_value", None) or crypto.token_amount or 0.0)
                matched_type = "CRYPTO"
            elif tgt_txn:
                matched_id = tgt_txn.id
                matched_identifier = getattr(tgt_txn, "external_transaction_id", getattr(tgt_txn, "transaction_id", tgt_txn.id))
                matched_type = tgt_txn.source_type or "TRANSACTION"
                matched_entity = getattr(tgt_txn, "counterparty_name", None)
                matched_date = tgt_txn.transaction_date.isoformat() if getattr(tgt_txn, "transaction_date", None) else None
                if d.discrepancy_type == "AMOUNT" and d.matched_value:
                    try:
                        matched_amount = float(d.matched_value)
                    except (ValueError, TypeError):
                        matched_amount = float(tgt_txn.amount)
                else:
                    matched_amount = float(tgt_txn.amount)
            elif d.discrepancy_type == "MISSING_ENTRY":
                matched_id = "missing"
                matched_identifier = "None (Missing in Ledger)"
                matched_amount = 0.0
                matched_type = "UNRECORDED"
                matched_entity = "Missing Counterparty"

            results.append({
                "id": d.id,
                "case_id": d.case_id,
                "match_id": d.match_id,
                "discrepancy_type": d.discrepancy_type,
                "field_name": d.field_name,
                "source_value": d.source_value,
                "matched_value": d.matched_value,
                "difference_numeric": float(d.difference_numeric or 0.0),
                "difference_percentage": d.difference_percentage,
                "root_cause_category": d.root_cause_category,
                "severity": d.severity,
                "status": d.status,
                "case_id": d.case_id,
                "case_number": d.case.case_number if d.case else None,
                "assigned_reviewer": d.case.assigned_reviewer_id if d.case else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "match_status": match.match_status if match else "UNMATCHED",
                "confidence_score": match.confidence_score if match else 0.0,
                "source_record": {
                    "id": src_txn.id if src_txn else (d.source_value or d.id),
                    "transaction_id": getattr(src_txn, "external_transaction_id", getattr(src_txn, "transaction_id", src_txn.id)) if src_txn else (d.source_value or "—"),
                    "amount": src_amount,
                    "currency": src_txn.currency if src_txn else "INR",
                    "source_type": src_txn.source_type if src_txn else "BANK",
                    "reference": src_txn.payment_reference if src_txn else None,
                    "date": src_txn.transaction_date.isoformat() if getattr(src_txn, "transaction_date", None) else None,
                    "entity_name": getattr(src_txn, "counterparty_name", None),
                },
                "matched_record": {
                    "id": matched_id,
                    "identifier": matched_identifier or "None (Missing Entry)",
                    "amount": matched_amount,
                    "type": matched_type,
                    "entity_name": matched_entity,
                    "date": matched_date,
                } if matched_id else None,
            })

        return results

    @classmethod
    def get_exception_detail(cls, db: Session, exception_id: str) -> Optional[Dict[str, Any]]:
        d = db.query(DiscrepancyRecord).filter(DiscrepancyRecord.id == exception_id).first()
        if not d:
            return None

        reviews = db.query(ManualReview).filter(ManualReview.match_id == d.match_id).order_by(ManualReview.created_at.desc()).all()
        audits = db.query(AuditLog).filter(AuditLog.entity_id == d.id).order_by(AuditLog.timestamp.desc()).all()

        match = db.query(ReconciliationMatch).filter(ReconciliationMatch.id == d.match_id).first() if d.match_id else None
        case = db.query(ReconciliationCase).filter(ReconciliationCase.id == d.case_id).first() if d.case_id else None

        evidence_list = []
        if match and match.evidence_json:
            try:
                evidence_list = json.loads(match.evidence_json)
            except Exception:
                pass

        return {
            "id": d.id,
            "case_id": d.case_id,
            "case_number": case.case_number if case else None,
            "match_id": d.match_id,
            "discrepancy_type": d.discrepancy_type,
            "field_name": d.field_name,
            "source_value": d.source_value,
            "matched_value": d.matched_value,
            "difference_numeric": float(d.difference_numeric or 0.0),
            "difference_percentage": d.difference_percentage,
            "root_cause_category": d.root_cause_category,
            "severity": d.severity,
            "status": d.status,
            "assigned_reviewer": case.assigned_reviewer_id if case else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "evidence": evidence_list,
            "reviews": [
                {
                    "id": r.id,
                    "reviewer_name": r.reviewer_name,
                    "action": r.action,
                    "previous_status": r.previous_status,
                    "new_status": r.new_status,
                    "notes": r.notes,
                    "created_at": r.created_at.isoformat(),
                }
                for r in reviews
            ],
            "audit_trail": [
                {
                    "id": a.id,
                    "action": a.action,
                    "actor_id": a.actor_id,
                    "details": a.details,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in audits
            ],
        }

    @classmethod
    def execute_action(
        cls,
        db: Session,
        exception_id: str,
        reviewer_name: str,
        action: str,
        notes: Optional[str] = None,
        adjustment_amount: Optional[float] = None,
        ip_address: Optional[str] = "127.0.0.1",
        assigned_to: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        d = db.query(DiscrepancyRecord).filter(DiscrepancyRecord.id == exception_id).first()
        if not d:
            return None

        match = db.query(ReconciliationMatch).filter(ReconciliationMatch.id == d.match_id).first() if d.match_id else None
        case = db.query(ReconciliationCase).filter(ReconciliationCase.id == d.case_id).first() if d.case_id else None

        old_state = {"status": d.status, "severity": d.severity}
        now = datetime.now(timezone.utc)

        act = action.upper().strip()
        if act == "CONFIRM_MATCH":
            d.status = "RESOLVED"
            if match:
                match.match_status = "EXACT_MATCH"
        elif act == "REJECT_MATCH":
            d.status = "RESOLVED"
            if match:
                match.match_status = "UNMATCHED"
        elif act == "WRITE_OFF":
            d.status = "WRITTEN_OFF"
            if match:
                match.match_status = "EXACT_MATCH"
        elif act == "MARK_DUPLICATE":
            d.status = "RESOLVED"
            if match:
                match.match_status = "DUPLICATE"
        elif act == "MARK_MISSING":
            d.status = "RESOLVED"
            if match:
                match.match_status = "MISSING_RECORD"
        elif act == "ESCALATE":
            d.status = "ESCALATED"
            d.severity = "CRITICAL"
            if case:
                case.priority = "CRITICAL"
                case.status = "ESCALATED"
        elif act == "ASSIGN_AUDITOR":
            d.status = "UNDER_REVIEW"
            target_auditor = assigned_to or notes or "Elena Rostova"
            if case:
                case.status = "UNDER_REVIEW"
                case.assigned_reviewer_id = target_auditor
        elif act == "ADD_NOTE":
            d.status = "UNDER_REVIEW"

        new_state = {"status": d.status, "severity": d.severity}

        # Persist ManualReview
        review = ManualReview(
            id=str(uuid.uuid4()),
            case_id=d.case_id,
            match_id=d.match_id,
            reviewer_name=reviewer_name,
            action=act,
            previous_status=old_state["status"],
            new_status=new_state["status"],
            notes=notes or f"Action {act} applied via Exception Workbench",
            created_at=now,
        )
        db.add(review)

        # Persist immutable AuditLog with cryptographic SHA-256 chained hash
        AuditService.create_log(
            db=db,
            entity_type="DISCREPANCY",
            entity_id=d.id,
            case_id=d.case_id,
            actor_type="MANUAL_REVIEWER",
            actor_id=reviewer_name,
            action=f"EXCEPTION_{act}",
            old_state=old_state,
            new_state=new_state,
            details=notes or f"Manual action {act} applied on discrepancy {d.id}",
            ip_address=ip_address,
        )

        db.commit()
        db.refresh(d)

        return {
            "exception_id": d.id,
            "status": d.status,
            "severity": d.severity,
            "action_executed": act,
            "reviewer": reviewer_name,
            "review_id": review.id,
            "timestamp": now.isoformat(),
        }

    @classmethod
    def execute_bulk_actions(
        cls,
        db: Session,
        exception_ids: List[str],
        reviewer_name: str,
        action: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        count = 0
        for eid in exception_ids:
            res = cls.execute_action(
                db=db,
                exception_id=eid,
                reviewer_name=reviewer_name,
                action=action,
                notes=notes,
            )
            if res:
                count += 1

        return {
            "total_requested": len(exception_ids),
            "successfully_updated": count,
            "action": action,
            "reviewer": reviewer_name,
        }

    @classmethod
    def get_summary(cls, db: Session) -> Dict[str, Any]:
        discrepancies = db.query(DiscrepancyRecord).all()

        total_open = 0
        crit_count = 0
        high_count = 0
        med_count = 0
        low_count = 0
        total_variance = 0.0

        by_root_cause = defaultdict(int)
        by_type = defaultdict(int)

        for d in discrepancies:
            if d.status in ["OPEN", "UNDER_REVIEW", "ESCALATED"]:
                total_open += 1

            if d.severity == "CRITICAL":
                crit_count += 1
            elif d.severity == "HIGH":
                high_count += 1
            elif d.severity == "MEDIUM":
                med_count += 1
            elif d.severity == "LOW":
                low_count += 1

            if d.difference_numeric:
                total_variance += abs(float(d.difference_numeric))

            if d.root_cause_category:
                by_root_cause[d.root_cause_category] += 1
            by_type[d.discrepancy_type] += 1

        summary = ExceptionSummaryResponse(
            total_open=total_open,
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            total_variance_usd=total_variance,
            by_root_cause=dict(by_root_cause),
            by_discrepancy_type=dict(by_type),
        )
        return summary.to_dict()
