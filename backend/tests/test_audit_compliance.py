import csv
import io
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.audit_log import AuditLog
from app.services.audit.service import AuditService, GENESIS_HASH
from app.services.audit.models import AuditLogFilter


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        # Ensure backfilled before test run
        AuditService.ensure_hashes_backfilled(db)
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestAuditCryptographicChain:
    def test_backfill_and_chain_structure(self, db_session):
        updated = AuditService.ensure_hashes_backfilled(db_session)
        logs = db_session.query(AuditLog).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc()).all()
        assert len(logs) > 0

        # Check genesis block
        genesis = logs[0]
        assert genesis.prev_hash == GENESIS_HASH
        assert genesis.entry_hash is not None
        assert len(genesis.entry_hash) == 64

        # Check continuous chain
        for i in range(1, len(logs)):
            prior = logs[i - 1]
            curr = logs[i]
            assert curr.prev_hash == prior.entry_hash
            assert curr.entry_hash is not None
            assert len(curr.entry_hash) == 64

    def test_verify_chain_integrity_healthy(self, db_session):
        verification = AuditService.verify_chain_integrity(db_session)
        assert verification.is_valid is True
        assert verification.total_blocks > 0
        assert verification.verified_blocks == verification.total_blocks
        assert len(verification.broken_blocks) == 0
        assert "SUCCESS" in verification.message

    def test_append_new_log_preserves_chain(self, db_session):
        initial_check = AuditService.verify_chain_integrity(db_session)
        assert initial_check.is_valid is True

        new_entry = AuditService.create_log(
            db=db_session,
            entity_type="TRANSACTION",
            entity_id="TXN-AUDIT-TEST-001",
            actor_type="MANUAL_REVIEWER",
            actor_id="Auditor John",
            action="MANUAL_OVERRIDE",
            details="Auditor manual validation test entry",
            case_id="CASE-TEST-01",
            old_state={"status": "FLAGGED"},
            new_state={"status": "APPROVED"},
            ip_address="192.168.1.10",
        )

        assert new_entry.id is not None
        assert new_entry.entry_hash is not None
        assert new_entry.prev_hash == initial_check.latest_hash

        # Re-verify
        post_check = AuditService.verify_chain_integrity(db_session)
        assert post_check.is_valid is True
        assert post_check.verified_blocks == initial_check.verified_blocks + 1
        assert post_check.latest_hash == new_entry.entry_hash

    def test_tamper_detection(self, db_session):
        # Pick the latest record and tamper with its details directly in DB
        latest = db_session.query(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).first()
        assert latest is not None
        original_details = latest.details

        try:
            # Inject malicious modification without re-signing
            latest.details = "MALICIOUS TAMPERED DETAIL: Unauthorized balance wipe"
            db_session.commit()

            # Verify that chain integrity catches the tampering
            tamper_check = AuditService.verify_chain_integrity(db_session)
            assert tamper_check.is_valid is False
            assert len(tamper_check.broken_blocks) > 0
            assert "WARNING" in tamper_check.message
            assert any("Hash mismatch" in reason for b in tamper_check.broken_blocks for reason in b["reasons"])
        finally:
            # Restore to preserve test isolation
            latest.details = original_details
            db_session.commit()
            # Re-verify restored state
            restored_check = AuditService.verify_chain_integrity(db_session)
            assert restored_check.is_valid is True


class TestAuditQueriesAndSummary:
    def test_query_filtering(self, db_session):
        # Filter by actor_type
        system_logs = AuditService.get_audit_logs(db_session, AuditLogFilter(actor_type="SYSTEM_ENGINE"))
        assert all(l.actor_type == "SYSTEM_ENGINE" for l in system_logs.items)

        # Filter by action
        action_filter = AuditService.get_audit_logs(db_session, AuditLogFilter(action="AUTO_MATCH_CREATED"))
        assert all(l.action == "AUTO_MATCH_CREATED" for l in action_filter.items)

        # Filter by free-text query
        query_res = AuditService.get_audit_logs(db_session, AuditLogFilter(query="Stripe"))
        assert query_res.total >= 1
        assert any("stripe" in l.details.lower() or "stripe" in l.action.lower() for l in query_res.items)

    def test_audit_summary_metrics(self, db_session):
        summary = AuditService.get_audit_summary(db_session)
        assert summary.total_events > 0
        assert summary.automated_events >= 1
        assert summary.manual_events >= 1
        assert summary.chain_status == "HEALTHY"
        assert summary.verified_blocks_count == summary.total_events
        assert "sox_404_four_eyes_assurance" in summary.compliance_controls
        assert summary.compliance_controls["sox_404_four_eyes_assurance"]["status"] == "PASS"
        assert "soc_2_type_ii_audit_logging" in summary.compliance_controls
        assert summary.compliance_controls["soc_2_type_ii_audit_logging"]["status"] == "PASS"

    def test_csv_export(self, db_session):
        csv_string = AuditService.export_csv(db_session)
        reader = csv.reader(io.StringIO(csv_string))
        rows = list(reader)
        assert len(rows) > 1
        header = rows[0]
        assert "Timestamp (UTC)" in header
        assert "Entry SHA-256 Hash" in header
        assert "Previous SHA-256 Hash" in header

    def test_compliance_package_export(self, db_session):
        pkg = AuditService.export_compliance_package(db_session)
        assert pkg.report_id.startswith("COMP-PKG-")
        assert "SOX Section 404" in pkg.standard
        assert pkg.chain_verification.is_valid is True
        assert len(pkg.event_logs) > 0


class TestAuditAPIEndpoints:
    def test_api_list_logs(self, client):
        resp = client.get("/api/v1/audit/logs?limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "entry_hash" in item
            assert "prev_hash" in item
            assert item["is_tamper_verified"] is True

    def test_api_summary(self, client):
        resp = client.get("/api/v1/audit/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] > 0
        assert data["chain_status"] == "HEALTHY"
        assert "compliance_controls" in data

    def test_api_verify_integrity(self, client):
        resp = client.post("/api/v1/audit/verify-integrity")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["total_blocks"] == data["verified_blocks"]
        assert len(data["broken_blocks"]) == 0

    def test_api_get_log_detail(self, client):
        list_resp = client.get("/api/v1/audit/logs?limit=1")
        log_id = list_resp.json()["items"][0]["id"]

        detail_resp = client.get(f"/api/v1/audit/logs/{log_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == log_id
        assert detail["entry_hash"] is not None

    def test_api_export_csv(self, client):
        resp = client.get("/api/v1/audit/export/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "finrecon_audit_trail_export.csv" in resp.headers.get("content-disposition", "")
        assert "Entry SHA-256 Hash" in resp.text

    def test_api_export_compliance_package(self, client):
        resp = client.get("/api/v1/audit/export/compliance-package")
        assert resp.status_code == 200
        data = resp.json()
        assert "report_id" in data
        assert "chain_verification" in data
        assert data["chain_verification"]["is_valid"] is True
