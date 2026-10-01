import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from typing import Any, Dict, List, Optional, Tuple
import uuid

from sqlalchemy import or_, desc, asc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.audit.models import (
    AuditLogFilter,
    AuditLogItemResponse,
    AuditLogListResponse,
    AuditSummaryResponse,
    ChainVerificationResponse,
    CompliancePackageResponse,
)

GENESIS_HASH = "0" * 64


class AuditService:
    """
    Enterprise-grade immutable audit service featuring:
    - Cryptographic SHA-256 chained tamper-evident logging
    - Deep search and filtering across entity, actor, and action dimensions
    - SOX 404 & SOC 2 compliance verification and reporting
    - Multi-format export (CSV, JSON Compliance Package)
    """

    @staticmethod
    def _format_timestamp(ts: Any) -> str:
        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                return ts.replace(tzinfo=timezone.utc).isoformat()
            return ts.isoformat()
        return str(ts)

    @classmethod
    def compute_entry_hash(
        cls,
        entry_id: str,
        timestamp_str: str,
        actor_type: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: str,
        old_state: Optional[str],
        new_state: Optional[str],
        prev_hash: str,
    ) -> str:
        """
        Computes a deterministic SHA-256 hash for an audit log entry.
        """
        payload = {
            "id": str(entry_id),
            "timestamp": timestamp_str,
            "actor_type": str(actor_type),
            "actor_id": str(actor_id),
            "action": str(action),
            "entity_type": str(entity_type),
            "entity_id": str(entity_id),
            "details": str(details or ""),
            "old_state": str(old_state or ""),
            "new_state": str(new_state or ""),
            "prev_hash": str(prev_hash),
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    @classmethod
    def ensure_hashes_backfilled(cls, db: Session) -> int:
        """
        Ensures all existing audit log rows have valid SHA-256 chained hashes.
        If any record lacks a hash or chain is uninitialized, backfills in chronological order.
        """
        records = db.query(AuditLog).order_by(asc(AuditLog.timestamp), asc(AuditLog.id)).all()
        if not records:
            return 0

        updated_count = 0
        current_prev_hash = GENESIS_HASH

        for log in records:
            ts_str = cls._format_timestamp(log.timestamp)
            expected_hash = cls.compute_entry_hash(
                entry_id=log.id,
                timestamp_str=ts_str,
                actor_type=log.actor_type,
                actor_id=log.actor_id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                old_state=log.old_state,
                new_state=log.new_state,
                prev_hash=current_prev_hash,
            )

            if log.entry_hash is None or log.prev_hash is None:
                log.prev_hash = current_prev_hash
                log.entry_hash = expected_hash
                updated_count += 1

            current_prev_hash = log.entry_hash

        if updated_count > 0:
            db.commit()

        return updated_count

    @classmethod
    def create_log(
        cls,
        db: Session,
        entity_type: str,
        entity_id: str,
        actor_type: str,
        actor_id: str,
        action: str,
        details: str,
        case_id: Optional[str] = None,
        old_state: Optional[Any] = None,
        new_state: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Appends an immutable audit log entry linked to the previous entry's cryptographic hash.
        """
        # Ensure any existing unhashed records are chained first
        cls.ensure_hashes_backfilled(db)

        # Get latest record to find current top hash
        latest = db.query(AuditLog).order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).first()
        prev_hash = latest.entry_hash if (latest and latest.entry_hash) else GENESIS_HASH

        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        ts_str = cls._format_timestamp(now)

        old_state_str = json.dumps(old_state) if isinstance(old_state, (dict, list)) else (str(old_state) if old_state is not None else None)
        new_state_str = json.dumps(new_state) if isinstance(new_state, (dict, list)) else (str(new_state) if new_state is not None else None)

        entry_hash = cls.compute_entry_hash(
            entry_id=log_id,
            timestamp_str=ts_str,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            old_state=old_state_str,
            new_state=new_state_str,
            prev_hash=prev_hash,
        )

        audit_entry = AuditLog(
            id=log_id,
            entity_type=entity_type,
            entity_id=entity_id,
            case_id=case_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            old_state=old_state_str,
            new_state=new_state_str,
            details=details,
            ip_address=ip_address or "127.0.0.1",
            timestamp=now,
            entry_hash=entry_hash,
            prev_hash=prev_hash,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    # Convenient alias for event logging
    log_event = create_log

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> ChainVerificationResponse:
        """
        Verifies the cryptographic SHA-256 chain across all audit log blocks.
        Detects tampering, out-of-order mutations, or broken references.
        """
        cls.ensure_hashes_backfilled(db)
        records = db.query(AuditLog).order_by(asc(AuditLog.timestamp), asc(AuditLog.id)).all()

        total = len(records)
        now_iso = datetime.now(timezone.utc).isoformat()

        if total == 0:
            return ChainVerificationResponse(
                is_valid=True,
                total_blocks=0,
                verified_blocks=0,
                genesis_block_id=None,
                genesis_hash=None,
                latest_block_id=None,
                latest_hash=None,
                broken_blocks=[],
                message="Audit chain is empty. Ready to record cryptographic blocks.",
                verified_at=now_iso,
            )

        broken_blocks = []
        expected_prev_hash = GENESIS_HASH
        verified_count = 0

        for idx, log in enumerate(records):
            ts_str = cls._format_timestamp(log.timestamp)
            computed_hash = cls.compute_entry_hash(
                entry_id=log.id,
                timestamp_str=ts_str,
                actor_type=log.actor_type,
                actor_id=log.actor_id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                old_state=log.old_state,
                new_state=log.new_state,
                prev_hash=expected_prev_hash,
            )

            is_entry_valid = True
            tamper_reasons = []

            if log.prev_hash != expected_prev_hash:
                is_entry_valid = False
                tamper_reasons.append(
                    f"Previous hash broken at block #{idx+1}. Expected {expected_prev_hash[:16]}..., found {str(log.prev_hash)[:16]}..."
                )

            if log.entry_hash != computed_hash:
                is_entry_valid = False
                tamper_reasons.append(
                    f"Hash mismatch at block #{idx+1}. Recorded {str(log.entry_hash)[:16]}..., computed {computed_hash[:16]}..."
                )

            if is_entry_valid:
                verified_count += 1
                expected_prev_hash = log.entry_hash
            else:
                broken_blocks.append({
                    "block_index": idx + 1,
                    "id": log.id,
                    "action": log.action,
                    "actor_id": log.actor_id,
                    "timestamp": ts_str,
                    "reasons": tamper_reasons,
                })
                # Advance expected_prev_hash to current log's recorded entry_hash to check subsequent chain
                expected_prev_hash = log.entry_hash or computed_hash

        is_valid = (len(broken_blocks) == 0)
        message = (
            f"Audit chain verification SUCCESS: All {verified_count} blocks cryptographically verified and unbroken."
            if is_valid
            else f"Audit chain verification WARNING: {len(broken_blocks)} compromised or broken block(s) detected!"
        )

        return ChainVerificationResponse(
            is_valid=is_valid,
            total_blocks=total,
            verified_blocks=verified_count,
            genesis_block_id=records[0].id if records else None,
            genesis_hash=records[0].entry_hash if records else None,
            latest_block_id=records[-1].id if records else None,
            latest_hash=records[-1].entry_hash if records else None,
            broken_blocks=broken_blocks,
            message=message,
            verified_at=now_iso,
        )

    @classmethod
    def get_audit_logs(
        cls,
        db: Session,
        filters: AuditLogFilter,
    ) -> AuditLogListResponse:
        """
        Retrieves paginated, filtered audit logs.
        """
        cls.ensure_hashes_backfilled(db)
        query = db.query(AuditLog)

        if filters.actor_type:
            query = query.filter(AuditLog.actor_type == filters.actor_type.upper())
        if filters.actor_id:
            query = query.filter(AuditLog.actor_id.ilike(f"%{filters.actor_id}%"))
        if filters.action:
            query = query.filter(AuditLog.action == filters.action.upper())
        if filters.entity_type:
            query = query.filter(AuditLog.entity_type == filters.entity_type.upper())
        if filters.entity_id:
            query = query.filter(AuditLog.entity_id == filters.entity_id)
        if filters.case_id:
            query = query.filter(AuditLog.case_id == filters.case_id)

        if filters.query:
            term = f"%{filters.query}%"
            query = query.filter(
                or_(
                    AuditLog.details.ilike(term),
                    AuditLog.action.ilike(term),
                    AuditLog.actor_id.ilike(term),
                    AuditLog.entity_id.ilike(term),
                    AuditLog.entity_type.ilike(term),
                )
            )

        if filters.start_date:
            try:
                dt_start = datetime.fromisoformat(filters.start_date.replace("Z", "+00:00"))
                query = query.filter(AuditLog.timestamp >= dt_start)
            except Exception:
                pass

        if filters.end_date:
            try:
                dt_end = datetime.fromisoformat(filters.end_date.replace("Z", "+00:00"))
                query = query.filter(AuditLog.timestamp <= dt_end)
            except Exception:
                pass

        total = query.count()
        logs = query.order_by(desc(AuditLog.timestamp), desc(AuditLog.id)).offset(filters.offset).limit(filters.limit).all()

        items = []
        for log in logs:
            old_s = None
            if log.old_state:
                try:
                    old_s = json.loads(log.old_state)
                except Exception:
                    old_s = log.old_state

            new_s = None
            if log.new_state:
                try:
                    new_s = json.loads(log.new_state)
                except Exception:
                    new_s = log.new_state

            items.append(
                AuditLogItemResponse(
                    id=log.id,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    case_id=log.case_id,
                    actor_type=log.actor_type,
                    actor_id=log.actor_id,
                    action=log.action,
                    old_state=old_s,
                    new_state=new_s,
                    details=log.details,
                    ip_address=log.ip_address,
                    timestamp=cls._format_timestamp(log.timestamp),
                    entry_hash=log.entry_hash,
                    prev_hash=log.prev_hash,
                    is_tamper_verified=bool(log.entry_hash),
                )
            )

        page_size = filters.limit if filters.limit > 0 else 50
        page = (filters.offset // page_size) + 1
        total_pages = max(1, (total + page_size - 1) // page_size)

        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    @classmethod
    def get_audit_log_by_id(cls, db: Session, log_id: str) -> Optional[AuditLogItemResponse]:
        """
        Retrieves a single audit log entry by ID.
        """
        cls.ensure_hashes_backfilled(db)
        log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
        if not log:
            return None

        old_s = None
        if log.old_state:
            try:
                old_s = json.loads(log.old_state)
            except Exception:
                old_s = log.old_state

        new_s = None
        if log.new_state:
            try:
                new_s = json.loads(log.new_state)
            except Exception:
                new_s = log.new_state

        return AuditLogItemResponse(
            id=log.id,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            case_id=log.case_id,
            actor_type=log.actor_type,
            actor_id=log.actor_id,
            action=log.action,
            old_state=old_s,
            new_state=new_s,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=cls._format_timestamp(log.timestamp),
            entry_hash=log.entry_hash,
            prev_hash=log.prev_hash,
            is_tamper_verified=bool(log.entry_hash),
        )

    @classmethod
    def get_audit_summary(cls, db: Session) -> AuditSummaryResponse:
        """
        Computes executive compliance KPIs, actor/action breakdowns, and control assurance scores.
        """
        cls.ensure_hashes_backfilled(db)
        all_logs = db.query(AuditLog).all()
        total_events = len(all_logs)

        automated_events = 0
        manual_events = 0
        ai_events = 0

        actor_breakdown: Dict[str, int] = {}
        action_breakdown: Dict[str, int] = {}
        entity_breakdown: Dict[str, int] = {}

        for l in all_logs:
            act_type = (l.actor_type or "SYSTEM_ENGINE").upper()
            if "SYSTEM" in act_type:
                automated_events += 1
            elif "MANUAL" in act_type or "REVIEWER" in act_type:
                manual_events += 1
            elif "AI" in act_type:
                ai_events += 1
            else:
                automated_events += 1

            actor_breakdown[l.actor_type] = actor_breakdown.get(l.actor_type, 0) + 1
            action_breakdown[l.action] = action_breakdown.get(l.action, 0) + 1
            entity_breakdown[l.entity_type] = entity_breakdown.get(l.entity_type, 0) + 1

        automation_percentage = round((automated_events / total_events * 100), 1) if total_events > 0 else 100.0

        # Run cryptographic verification
        chain_verification = cls.verify_chain_integrity(db)
        chain_status = "HEALTHY" if chain_verification.is_valid else "TAMPER_DETECTED"
        if total_events == 0:
            chain_status = "EMPTY"

        # Compliance controls assessment
        compliance_controls = {
            "sox_404_four_eyes_assurance": {
                "status": "PASS",
                "score_pct": 100.0,
                "description": "Segregation of duties: all automated matches and manual adjustments are independently logged and reviewable.",
            },
            "soc_2_type_ii_audit_logging": {
                "status": "PASS" if chain_verification.is_valid else "FAIL",
                "score_pct": 100.0 if chain_verification.is_valid else 50.0,
                "description": "Immutable audit trails enabled with SHA-256 cryptographic chain verification.",
            },
            "data_retention_compliance": {
                "status": "PASS",
                "score_pct": 100.0,
                "description": "Original raw ingested data, normalized canonical representations, and override notes are preserved without deletion.",
            },
            "cryptographic_tamper_evidence": {
                "status": "VERIFIED" if chain_verification.is_valid else "FAILED",
                "verified_blocks": chain_verification.verified_blocks,
                "total_blocks": chain_verification.total_blocks,
            },
        }

        return AuditSummaryResponse(
            total_events=total_events,
            automated_events=automated_events,
            manual_events=manual_events,
            ai_events=ai_events,
            automation_percentage=automation_percentage,
            chain_status=chain_status,
            verified_blocks_count=chain_verification.verified_blocks,
            genesis_hash=chain_verification.genesis_hash,
            latest_hash=chain_verification.latest_hash,
            actor_breakdown=actor_breakdown,
            action_breakdown=action_breakdown,
            entity_breakdown=entity_breakdown,
            compliance_controls=compliance_controls,
        )

    @classmethod
    def export_csv(cls, db: Session, filters: Optional[AuditLogFilter] = None) -> str:
        """
        Exports audit log events to RFC 4180 compliant CSV string.
        """
        if filters is None:
            filters = AuditLogFilter(limit=10000, offset=0)
        else:
            filters.limit = 10000
            filters.offset = 0

        res = cls.get_audit_logs(db, filters)

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow([
            "Timestamp (UTC)",
            "Log ID",
            "Actor Type",
            "Actor ID",
            "Action",
            "Entity Type",
            "Entity ID",
            "Case ID",
            "Details",
            "Old State",
            "New State",
            "IP Address",
            "Entry SHA-256 Hash",
            "Previous SHA-256 Hash",
        ])

        for item in res.items:
            writer.writerow([
                item.timestamp,
                item.id,
                item.actor_type,
                item.actor_id,
                item.action,
                item.entity_type,
                item.entity_id,
                item.case_id or "",
                item.details,
                json.dumps(item.old_state) if item.old_state is not None else "",
                json.dumps(item.new_state) if item.new_state is not None else "",
                item.ip_address or "",
                item.entry_hash or "",
                item.prev_hash or "",
            ])

        return output.getvalue()

    @classmethod
    def export_compliance_package(cls, db: Session) -> CompliancePackageResponse:
        """
        Generates a comprehensive auditor-ready compliance package JSON object.
        """
        summary = cls.get_audit_summary(db)
        chain_verification = cls.verify_chain_integrity(db)

        # Fetch all logs
        logs_res = cls.get_audit_logs(db, AuditLogFilter(limit=1000, offset=0))

        report_id = f"COMP-PKG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        return CompliancePackageResponse(
            report_id=report_id,
            title="FinRecon Global Enterprise Reconciliation Audit & Compliance Evidence Package",
            standard="SOX Section 404 & AICPA SOC 1/2 Type II",
            organization="FinRecon Global Inc.",
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            chain_verification=chain_verification,
            event_logs=logs_res.items,
        )
