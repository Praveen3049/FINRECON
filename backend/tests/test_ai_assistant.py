import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.ai_assistant.service import AIAssistantService
from app.models.reconciliation_case import ReconciliationCase
from app.models.discrepancy_record import DiscrepancyRecord


from datetime import datetime, timezone
from decimal import Decimal
import uuid
from app.models.reconciliation_match import ReconciliationMatch
from app.models.discrepancy_record import DiscrepancyRecord


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    created_case_ids = []
    
    # Check if test cases exist
    test_cases_defs = [
        ("CASE-2026-0001", "Exact match test case", "RECONCILED", Decimal("0.0"), "MEDIUM"),
        ("CASE-2026-0002", "Payment Gateway Stripe fee netting case Starlight Tech", "UNDER_REVIEW", Decimal("580.00"), "MEDIUM"),
        ("CASE-2026-0004", "Duplicate Check #994821 presented twice", "ESCALATED", Decimal("15400.00"), "CRITICAL"),
        ("CASE-2026-0009", "Crypto ETH slippage case", "UNDER_REVIEW", Decimal("14.50"), "LOW"),
    ]
    
    for c_num, title, status_str, var_amt, prio in test_cases_defs:
        existing = db.query(ReconciliationCase).filter(ReconciliationCase.case_number == c_num).first()
        if not existing:
            c = ReconciliationCase(
                id=str(uuid.uuid4()),
                case_number=c_num,
                title=title,
                status=status_str,
                priority=prio,
                primary_source_type="PAYMENT_GATEWAY",
                total_variance_amount=var_amt,
                total_date_variance_days=0,
                created_at=datetime.now(timezone.utc),
            )
            db.add(c)
            created_case_ids.append(c.id)
    db.commit()

    try:
        yield db
    finally:
        if created_case_ids:
            db.query(ReconciliationCase).filter(ReconciliationCase.id.in_(created_case_ids)).delete(synchronize_session=False)
            db.commit()
        db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestAIAssistantService:
    def test_get_prebuilt_prompts(self):
        prompts = AIAssistantService.get_prebuilt_prompts()
        assert len(prompts) >= 5
        assert any("prompt-fee-variance" in p.id for p in prompts)
        assert any("prompt-crypto-slippage" in p.id for p in prompts)

    def test_explain_exact_match_case(self, db_session):
        explanation = AIAssistantService.explain_case(db_session, "CASE-2026-0001")
        assert explanation.case_number == "CASE-2026-0001"
        assert explanation.status == "RECONCILED"
        assert "exact match" in explanation.executive_summary.lower()
        assert len(explanation.facts) > 0
        assert len(explanation.calculated) > 0
        assert any(s.action == "CONFIRM_MATCH" for s in explanation.suggestions)

    def test_explain_gateway_fee_case(self, db_session):
        explanation = AIAssistantService.explain_case(db_session, "CASE-2026-0002")
        assert explanation.case_number == "CASE-2026-0002"
        assert "580.00" in explanation.executive_summary or "580" in explanation.executive_summary
        assert any("2.90%" in str(c.value) for c in explanation.calculated)
        assert explanation.suggested_journal_entry is not None
        je = explanation.suggested_journal_entry
        assert je.total_debit == 580.00
        assert je.total_credit == 580.00
        assert any(l.account_number == "6020" for l in je.lines)
        assert any(l.account_number == "1200" for l in je.lines)

    def test_explain_duplicate_check_case(self, db_session):
        explanation = AIAssistantService.explain_case(db_session, "CASE-2026-0004")
        assert explanation.case_number == "CASE-2026-0004"
        assert "994821" in explanation.executive_summary
        assert any(s.action == "ESCALATE" for s in explanation.suggestions)

    def test_explain_crypto_slippage_case(self, db_session):
        explanation = AIAssistantService.explain_case(db_session, "CASE-2026-0009")
        assert explanation.case_number == "CASE-2026-0009"
        assert "14.50" in explanation.executive_summary
        assert any("0.41%" in str(c.value) for c in explanation.calculated)
        assert any(s.action == "WRITE_OFF" for s in explanation.suggestions)
        assert explanation.suggested_journal_entry is not None
        assert any(l.account_number == "7010" for l in explanation.suggested_journal_entry.lines)

    def test_explain_discrepancy(self, db_session):
        disc = db_session.query(DiscrepancyRecord).first()
        assert disc is not None
        res = AIAssistantService.explain_discrepancy(db_session, disc.id)
        assert res.title is not None
        assert len(res.facts) > 0 or len(res.calculated) > 0

    def test_chat_query_specific_case(self, db_session):
        resp = AIAssistantService.answer_chat_query(
            db_session,
            query="Explain the $580.00 fee variance on CASE-2026-0002 (Starlight Tech)",
        )
        assert "CASE-2026-0002" in resp.answer
        assert len(resp.facts) > 0
        assert len(resp.calculated) > 0
        assert resp.suggested_journal_entry is not None
        assert len(resp.related_cases) >= 1

    def test_chat_query_critical_summary(self, db_session):
        resp = AIAssistantService.answer_chat_query(
            db_session,
            query="Summarize all open critical exceptions across bank statements and ERP ledgers.",
        )
        assert "active cases" in resp.answer.lower() or "critical" in resp.answer.lower()
        assert len(resp.facts) > 0
        assert len(resp.related_cases) > 0

    def test_chat_query_gateway_fees(self, db_session):
        resp = AIAssistantService.answer_chat_query(
            db_session,
            query="What journal adjustment entries should be booked for payment gateway fees?",
        )
        assert "6020" in resp.answer
        assert "Payment Gateway" in resp.answer
        assert len(resp.suggestions) > 0


class TestAIAssistantAPIEndpoints:
    def test_api_prompts(self, client):
        resp = client.get("/api/v1/ai-assistant/prompts")
        assert resp.status_code == 200
        prompts = resp.json()
        assert len(prompts) >= 5

    def test_api_chat(self, client):
        resp = client.post(
            "/api/v1/ai-assistant/chat",
            json={"query": "Explain CASE-2026-0002 fee variance"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "facts" in data
        assert "calculated" in data
        assert "suggestions" in data

    def test_api_explain_case(self, client):
        resp = client.post("/api/v1/ai-assistant/explain/case/CASE-2026-0002")
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_number"] == "CASE-2026-0002"
        assert len(data["facts"]) > 0
        assert len(data["calculated"]) > 0
        assert data["suggested_journal_entry"] is not None

    def test_api_explain_discrepancy(self, client, db_session):
        disc = db_session.query(DiscrepancyRecord).first()
        resp = client.post(f"/api/v1/ai-assistant/explain/discrepancy/{disc.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data

    def test_api_status(self, client):
        resp = client.get("/api/v1/ai-assistant/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "openai_configured" in data
        assert "active_engine" in data
        assert "model" in data

    def test_api_configure_key(self, client):
        test_key = "sk-test1234567890abcdefghijklmnopqrstuvwxyz"
        resp = client.post(
            "/api/v1/ai-assistant/configure-key",
            json={"api_key": test_key, "model": "gpt-4o"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["openai_configured"] is True
        assert data["model"] == "gpt-4o"
        assert "sk-test" in data["key_preview"]
        from app.services.ai_assistant.chatgpt_client import ChatGPTClient
        ChatGPTClient._runtime_key = None
