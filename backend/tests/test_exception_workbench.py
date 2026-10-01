import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models import DiscrepancyRecord, ManualReview, AuditLog
from app.services.exceptions.service import ExceptionWorkbenchService

client = TestClient(app)


class TestExceptionWorkbenchService:
    """Test unit execution of exception workflows, reviewer actions, and audit logs"""

    def test_get_exceptions_and_summary(self):
        db = SessionLocal()
        try:
            exceptions = ExceptionWorkbenchService.get_exceptions(db=db, limit=10)
            assert isinstance(exceptions, list)
            assert len(exceptions) > 0

            summary = ExceptionWorkbenchService.get_summary(db=db)
            assert "total_open" in summary
            assert "total_variance_usd" in summary
            assert "by_root_cause" in summary
            assert summary["total_open"] >= 0
        finally:
            db.close()

    def test_action_confirm_match(self):
        db = SessionLocal()
        try:
            disc = db.query(DiscrepancyRecord).first()
            assert disc is not None

            res = ExceptionWorkbenchService.execute_action(
                db=db,
                exception_id=disc.id,
                reviewer_name="Senior Controller Jack",
                action="CONFIRM_MATCH",
                notes="Verified with merchant receipt.",
            )
            assert res is not None
            assert res["status"] == "RESOLVED"
            assert res["action_executed"] == "CONFIRM_MATCH"

            # Check that an AuditLog was emitted
            audit = db.query(AuditLog).filter(
                AuditLog.entity_id == disc.id,
                AuditLog.action == "EXCEPTION_CONFIRM_MATCH",
            ).first()
            assert audit is not None
            assert audit.actor_id == "Senior Controller Jack"
        finally:
            db.close()

    def test_action_write_off(self):
        db = SessionLocal()
        try:
            disc = db.query(DiscrepancyRecord).first()
            assert disc is not None

            res = ExceptionWorkbenchService.execute_action(
                db=db,
                exception_id=disc.id,
                reviewer_name="Finance Analyst Bob",
                action="WRITE_OFF",
                notes="Minor variance within write-off limit.",
            )
            assert res is not None
            assert res["status"] == "WRITTEN_OFF"
        finally:
            db.close()

    def test_action_escalate(self):
        db = SessionLocal()
        try:
            disc = db.query(DiscrepancyRecord).first()
            assert disc is not None

            res = ExceptionWorkbenchService.execute_action(
                db=db,
                exception_id=disc.id,
                reviewer_name="Auditor Alice",
                action="ESCALATE",
                notes="Suspicious discrepancy requires senior management sign-off.",
            )
            assert res is not None
            assert res["status"] == "ESCALATED"
            assert res["severity"] == "CRITICAL"
        finally:
            db.close()

    def test_bulk_actions(self):
        db = SessionLocal()
        try:
            discs = db.query(DiscrepancyRecord).limit(2).all()
            ids = [d.id for d in discs]
            res = ExceptionWorkbenchService.execute_bulk_actions(
                db=db,
                exception_ids=ids,
                reviewer_name="Batch Job Reviewer",
                action="ADD_NOTE",
                notes="Automated periodic review check.",
            )
            assert res["successfully_updated"] == len(ids)
        finally:
            db.close()


class TestExceptionAPIEndpoints:
    """Test REST API endpoints for exception workbench"""

    def test_api_list_exceptions(self):
        res = client.get("/api/v1/exceptions?limit=5")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "discrepancy_type" in data[0]

    def test_api_summary(self):
        res = client.get("/api/v1/exceptions/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_open" in data
        assert "by_root_cause" in data

    def test_api_exception_detail_and_action(self):
        list_res = client.get("/api/v1/exceptions?limit=1")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) > 0
        eid = items[0]["id"]

        # Detail
        detail_res = client.get(f"/api/v1/exceptions/{eid}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == eid
        assert "audit_trail" in detail

        # Apply action
        action_payload = {
            "reviewer_name": "API Reviewer",
            "action": "CONFIRM_MATCH",
            "notes": "Validated via automated endpoint test.",
        }
        action_res = client.post(f"/api/v1/exceptions/{eid}/action", json=action_payload)
        assert action_res.status_code == 200
        act_data = action_res.json()
        assert act_data["status"] == "RESOLVED"
        assert act_data["reviewer"] == "API Reviewer"
