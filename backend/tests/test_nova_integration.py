import asyncio
import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from app.main import app
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.ai_assistant.nova_client import NovaClient
from app.services.ai_assistant.service import AIAssistantService
from app.models.reconciliation_case import ReconciliationCase


from datetime import datetime, timezone
from decimal import Decimal
import uuid
from app.models import (
    DataSource,
    Transaction,
    Invoice,
    CryptoTransaction,
    ReconciliationMatch,
    DiscrepancyRecord,
)


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    created_case_ids = []
    created_match_ids = []
    created_disc_ids = []
    created_crypto_ids = []
    created_src_ids = []
    created_tx_ids = []

    c2 = db.query(ReconciliationCase).filter(ReconciliationCase.case_number == "CASE-2026-0002").first()
    if not c2:
        c2 = ReconciliationCase(
            id=str(uuid.uuid4()),
            case_number="CASE-2026-0002",
            title="Starlight Tech payment gateway fee netting",
            status="UNDER_REVIEW",
            priority="MEDIUM",
            primary_source_type="PAYMENT_GATEWAY",
            total_variance_amount=Decimal("580.00"),
            total_date_variance_days=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(c2)
        created_case_ids.append(c2.id)

        src_gw = db.query(DataSource).filter(DataSource.source_type == "PAYMENT_GATEWAY").first()
        t2 = Transaction(
            id=str(uuid.uuid4()),
            source_id=src_gw.id if src_gw else "src_aczen_gateway",
            source_type="PAYMENT_GATEWAY",
            external_transaction_id="TXN-TEST-2002",
            amount=Decimal("19420.00"),
            fee_amount=Decimal("580.00"),
            net_amount=Decimal("19420.00"),
            currency="USD",
            direction="CREDIT",
            transaction_date=datetime.now(timezone.utc).date(),
            status="SETTLED",
        )
        db.add(t2)
        created_tx_ids.append(t2.id)

        m2 = ReconciliationMatch(
            id=str(uuid.uuid4()),
            case_id=c2.id,
            source_transaction_id=t2.id,
            match_type="TXN_TO_INVOICE",
            match_status="PARTIAL_MATCH",
            confidence_score=95.0,
            confidence_level="HIGH",
            algorithm_pass="PASS_3_GATEWAY_FEE_NETTING",
            created_at=datetime.now(timezone.utc),
        )
        db.add(m2)
        created_match_ids.append(m2.id)

        d2 = DiscrepancyRecord(
            id=str(uuid.uuid4()),
            case_id=c2.id,
            match_id=m2.id,
            discrepancy_type="AMOUNT",
            field_name="total_amount",
            source_value="19420.00",
            matched_value="20000.00",
            difference_numeric=Decimal("580.00"),
            difference_percentage=2.90,
            root_cause_category="PROCESSING_FEE",
            severity="MEDIUM",
            status="OPEN",
            created_at=datetime.now(timezone.utc),
        )
        db.add(d2)
        created_disc_ids.append(d2.id)

    c7 = db.query(ReconciliationCase).filter(ReconciliationCase.case_number == "CASE-2026-0007").first()
    if not c7:
        c7 = ReconciliationCase(
            id=str(uuid.uuid4()),
            case_number="CASE-2026-0007",
            title="Web3 Treasury USDT on-chain settlement",
            status="RECONCILED",
            priority="LOW",
            primary_source_type="CRYPTO",
            total_variance_amount=Decimal("0.0"),
            total_date_variance_days=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(c7)
        created_case_ids.append(c7.id)

        src = db.query(DataSource).filter(DataSource.source_type == "CRYPTO").first()
        if not src:
            src = DataSource(
                id="test_src_crypto_nova",
                name="Test Crypto Feed",
                source_type="CRYPTO",
                file_format="JSON",
                currency="USD",
                is_active=True,
            )
            db.add(src)
            created_src_ids.append(src.id)

        ctx = CryptoTransaction(
            id=str(uuid.uuid4()),
            source_id=src.id,
            blockchain_network="ETHEREUM",
            transaction_hash="0x7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
            wallet_from="0x1111111111111111111111111111111111111111",
            wallet_to="0x2222222222222222222222222222222222222222",
            asset="USDT",
            token_amount=Decimal("10000.0"),
            fiat_value=Decimal("10000.0"),
            fiat_currency="USD",
            gas_fee=Decimal("0.001"),
            gas_fee_fiat=Decimal("2.50"),
            block_number=18000000,
            confirmation_status="CONFIRMED",
            transaction_timestamp=datetime.now(timezone.utc),
        )
        db.add(ctx)
        created_crypto_ids.append(ctx.id)

        m7 = ReconciliationMatch(
            id=str(uuid.uuid4()),
            case_id=c7.id,
            crypto_transaction_id=ctx.id,
            match_type="CRYPTO_TO_INVOICE",
            match_status="EXACT_MATCH",
            confidence_score=100.0,
            confidence_level="HIGH",
            algorithm_pass="PASS_4_CRYPTO_ON_CHAIN",
            created_at=datetime.now(timezone.utc),
        )
        db.add(m7)
        created_match_ids.append(m7.id)

    db.commit()

    try:
        yield db
    finally:
        if created_disc_ids:
            db.query(DiscrepancyRecord).filter(DiscrepancyRecord.id.in_(created_disc_ids)).delete(synchronize_session=False)
        if created_match_ids:
            db.query(ReconciliationMatch).filter(ReconciliationMatch.id.in_(created_match_ids)).delete(synchronize_session=False)
        if created_case_ids:
            db.query(ReconciliationCase).filter(ReconciliationCase.id.in_(created_case_ids)).delete(synchronize_session=False)
        if created_tx_ids:
            db.query(Transaction).filter(Transaction.id.in_(created_tx_ids)).delete(synchronize_session=False)
        if created_crypto_ids:
            db.query(CryptoTransaction).filter(CryptoTransaction.id.in_(created_crypto_ids)).delete(synchronize_session=False)
        if created_src_ids:
            db.query(DataSource).filter(DataSource.id.in_(created_src_ids)).delete(synchronize_session=False)
        db.commit()
        db.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestNovaClientAndConfiguration:
    def test_nova_configuration_loading(self):
        assert settings.NOVA_API_BASE_URL == "https://www.aczen.in/nova-api/v1"
        assert settings.NOVA_TIMEOUT_SECONDS == 15.0

    def test_missing_api_key_handling(self):
        # Client with no key should report not configured and return None gracefully
        client = NovaClient(api_key="")
        assert client.is_configured is False
        result = asyncio.run(client.generate_explanation("test prompt", "test system"))
        assert result is None

    def test_nova_client_auth_and_success_mock(self):
        fake_key = "test_nova_sk_live_12345"
        client = NovaClient(api_key=fake_key)
        assert client.is_configured is True

        mock_response = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "summary": "Reconciled with gateway fee withholding.",
                                "why_flagged": "2.9% fee withheld at Stripe checkout.",
                                "explanation": "Gross invoice was $20,000 while deposit was $19,420.",
                                "reviewer_attention": "Verify merchant fee rate schedule.",
                                "suggested_next_checks": ["Check Stripe balance transaction detail", "Post adjustment to Account 6020"],
                            })
                        }
                    }
                ]
            },
            request=httpx.Request("POST", f"{client.base_url}/chat/completions"),
        )

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            output = asyncio.run(client.generate_explanation("prompt", "system"))

            assert output is not None
            assert "gateway fee" in output.lower()

            # Verify Bearer token was sent correctly
            called_headers = mock_post.call_args[1]["headers"]
            assert called_headers["Authorization"] == f"Bearer {fake_key}"

    def test_nova_api_timeout_fallback(self):
        client = NovaClient(api_key="mock_key")
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):
            output = asyncio.run(client.generate_explanation("prompt", "system"))
            assert output is None

    def test_nova_api_http_error_fallback(self):
        client = NovaClient(api_key="mock_key")
        mock_err_response = httpx.Response(
            status_code=500,
            request=httpx.Request("POST", "https://www.aczen.in/nova-api/v1/chat/completions"),
        )
        with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError("500 Server Error", request=mock_err_response.request, response=mock_err_response)):
            output = asyncio.run(client.generate_explanation("prompt", "system"))
            assert output is None


class TestReconciliationEvidenceAndInvestigation:
    def test_structured_reconciliation_evidence(self, db_session):
        case = db_session.query(ReconciliationCase).filter(ReconciliationCase.case_number == "CASE-2026-0002").first()
        assert case is not None

        evidence = AIAssistantService.build_structured_evidence(db_session, case)
        assert evidence["case_number"] == "CASE-2026-0002"
        assert evidence["total_variance_amount"] == 580.0
        assert len(evidence["sources"]) >= 1
        assert len(evidence["discrepancies"]) >= 1
        assert evidence["confidence"] > 0

    def test_crypto_support_in_evidence(self, db_session):
        crypto_case = db_session.query(ReconciliationCase).filter(ReconciliationCase.case_number == "CASE-2026-0007").first()
        assert crypto_case is not None

        evidence = AIAssistantService.build_structured_evidence(db_session, crypto_case)
        assert "crypto_records" in evidence
        assert len(evidence["crypto_records"]) > 0
        record = evidence["crypto_records"][0]
        assert record["blockchain_network"] == "ETHEREUM"
        assert record["asset"] == "USDT"
        assert record["token_amount"] == 10000.0
        assert record["gas_fee_fiat"] is not None

    def test_investigation_deterministic_fallback(self, db_session):
        # Force Nova to be unconfigured
        with patch.object(NovaClient, "is_configured", False):
            res = asyncio.run(AIAssistantService.investigate_case_with_nova(
                db_session,
                case_identifier="CASE-2026-0002",
                question="What caused the $580.00 discrepancy?",
            ))
            assert res.case_number == "CASE-2026-0002"
            assert res.ai_provider == "DETERMINISTIC_FALLBACK"
            assert "Stripe" in res.why_flagged or "Gateway" in res.why_flagged
            assert len(res.suggested_next_checks) >= 2
            assert res.reviewer_attention is not None
            assert res.suggested_journal_entry is not None
            assert res.suggested_journal_entry.total_debit == 580.0

    def test_investigation_with_mocked_nova(self, db_session):
        mock_nova_answer = json.dumps({
            "summary": "Verified Starlight Tech Invoice INV-2026-2002 reconciled against Stripe with standard processing fee deduction.",
            "why_flagged": "Gross customer billing of $20,000 differed from net bank deposit of $19,420 due to standard 2.9% merchant discount rate.",
            "explanation": "Stripe withheld exactly $580.00 at transaction settlement. Net payment posted to Chase Operating Account.",
            "reviewer_attention": "Ensure fee schedule conforms to merchant agreement before booking Account 6020 adjustment.",
            "suggested_next_checks": [
                "Verify Stripe payout batch reference",
                "Confirm Account 6020 debit of $580.00",
                "Close invoice in ERP",
            ],
        })

        with patch.object(NovaClient, "is_configured", True):
            with patch.object(NovaClient, "generate_explanation", new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = mock_nova_answer
                res = asyncio.run(AIAssistantService.investigate_case_with_nova(
                    db_session,
                    case_identifier="CASE-2026-0002",
                    question="Why was this transaction flagged?",
                ))

                assert res.case_number == "CASE-2026-0002"
                assert res.ai_provider == "NOVA_AI"
                assert "Starlight Tech" in res.summary
                assert len(res.suggested_next_checks) == 3


class TestSecurityAndEndpoints:
    def test_health_check_does_not_leak_key(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "nova_configured" in data
        assert isinstance(data["nova_configured"], bool)
        # Verify no secret fields exist in response
        assert "NOVA_API_KEY" not in data
        assert "api_key" not in data
        assert "authorization" not in data

    def test_explain_endpoint_integration(self, client, db_session):
        resp = client.post(
            "/api/v1/ai-assistant/explain",
            json={
                "reconciliation_case_id": "CASE-2026-0002",
                "question": "What caused the discrepancy?",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["case_number"] == "CASE-2026-0002"
        assert "why_flagged" in data
        assert "reviewer_attention" in data
        assert "suggested_next_checks" in data
        assert "ai_provider" in data
        # Ensure raw secrets never leaked
        serialized = json.dumps(data)
        assert "Bearer" not in serialized
        assert "sk-" not in serialized

    def test_step_11_health_diagnostics_reports_nova_configured_strictly(self, client):
        for endpoint in ["/api/v1/health/diagnostics", "/api/v1/config"]:
            resp = client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert "NOVA_CONFIGURED" in data
            assert isinstance(data["NOVA_CONFIGURED"], bool)
            assert "DATABASE_CONNECTED" in data
            # Strict Step 11 Security Rules:
            assert "NOVA_API_KEY" not in data
            assert "api_key" not in data
            assert "authorization" not in data
            assert "Authorization" not in data
            serialized = json.dumps(data)
            assert "Bearer" not in serialized

    def test_step_11_unconfigured_nova_reports_false(self, client):
        with patch.object(settings, "NOVA_API_KEY", ""):
            resp = client.get("/api/v1/health/diagnostics")
            assert resp.status_code == 200
            data = resp.json()
            assert data["NOVA_CONFIGURED"] is False
            assert "NOVA_API_KEY" not in data


class TestStep12TenScenarios:
    """
    Direct verification of all 10 FIN-26 Step 12 testing requirements:
    1. Nova configuration loading
    2. Missing API key handling
    3. Nova client authentication
    4. Nova API success response
    5. Nova API timeout
    6. Nova API failure
    7. AI investigation service
    8. Structured reconciliation evidence passed to AI
    9. Frontend/backend AI endpoint integration
    10. Secret leakage prevention
    """

    # 1. Nova configuration loading
    def test_scenario_1_configuration_loading(self):
        assert settings.NOVA_API_BASE_URL.startswith("http")
        assert isinstance(settings.NOVA_TIMEOUT_SECONDS, (int, float))

    # 2. Missing API key handling
    def test_scenario_2_missing_api_key_handling(self):
        empty_client = NovaClient(api_key="")
        assert empty_client.is_configured is False
        assert asyncio.run(empty_client.generate_explanation("prompt", "system")) is None

    # 3. Nova client authentication
    def test_scenario_3_client_authentication_header(self):
        mock_key = "test_key_xyz_789"
        client = NovaClient(api_key=mock_key)
        mock_resp = httpx.Response(
            200,
            json={"choices": [{"message": {"content": "{\"summary\": \"OK\"}"}}]},
            request=httpx.Request("POST", client.base_url)
        )
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            asyncio.run(client.generate_explanation("prompt", "system"))
            assert mock_post.call_args[1]["headers"]["Authorization"] == f"Bearer {mock_key}"

    # 4. Nova API success response
    def test_scenario_4_api_success_response(self):
        client = NovaClient(api_key="mock_key")
        mock_payload = {
            "summary": "Verified match",
            "why_flagged": "Exact match across sources",
            "explanation": "No variance found",
            "reviewer_attention": "None",
            "suggested_next_checks": ["Archive case"]
        }
        mock_resp = httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(mock_payload)}}]},
            request=httpx.Request("POST", client.base_url)
        )
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            output = asyncio.run(client.generate_explanation("prompt", "system"))
            assert output is not None
            parsed = json.loads(output)
            assert parsed["summary"] == "Verified match"

    # 5. Nova API timeout
    def test_scenario_5_api_timeout_handling(self):
        client = NovaClient(api_key="mock_key")
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
            output = asyncio.run(client.generate_explanation("prompt", "system"))
            assert output is None

    # 6. Nova API failure
    def test_scenario_6_api_failure_handling(self):
        client = NovaClient(api_key="mock_key")
        mock_resp = httpx.Response(502, request=httpx.Request("POST", client.base_url))
        with patch("httpx.AsyncClient.post", side_effect=httpx.HTTPStatusError("Bad Gateway", request=mock_resp.request, response=mock_resp)):
            output = asyncio.run(client.generate_explanation("prompt", "system"))
            assert output is None

    # 7. AI investigation service
    def test_scenario_7_ai_investigation_service(self, db_session):
        res = asyncio.run(AIAssistantService.investigate_case_with_nova(
            db_session,
            case_identifier="CASE-2026-0002",
            question="Why was this flagged?"
        ))
        assert res.case_number == "CASE-2026-0002"
        assert res.confidence_score > 0
        assert res.status in ["UNDER_REVIEW", "RECONCILED", "OPEN"]
        assert len(res.facts) > 0

    # 8. Structured reconciliation evidence passed to AI
    def test_scenario_8_structured_evidence_generation(self, db_session):
        case = db_session.query(ReconciliationCase).first()
        evidence = AIAssistantService.build_structured_evidence(db_session, case)
        assert "case_number" in evidence
        assert "sources" in evidence
        assert "discrepancies" in evidence
        assert "confidence" in evidence

    # 9. Frontend/backend AI endpoint integration
    def test_scenario_9_frontend_backend_endpoint_integration(self, client):
        resp = client.post(
            "/api/v1/ai-assistant/explain",
            json={"reconciliation_case_id": "CASE-2026-0002", "question": "Explain this case"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "matched_evidence" in data
        assert "discrepancies" in data
        assert "reviewer_attention" in data
        assert "suggested_next_checks" in data

    # 10. Secret leakage prevention
    def test_scenario_10_secret_leakage_prevention(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        content = resp.text
        assert "NOVA_API_KEY" not in content
        assert "Bearer" not in content

        diag_resp = client.get("/api/v1/health/diagnostics")
        assert diag_resp.status_code == 200
        diag_content = diag_resp.text
        assert "NOVA_API_KEY" not in diag_content
        assert "Bearer" not in diag_content

    # Step 14: Architectural Rule Enforcement
    def test_step_14_architecture_rule_deterministic_engine_is_source_of_truth(self, db_session):
        """
        FIN-26 Step 14: IMPORTANT ARCHITECTURE RULE
        Verifies that:
        1. Nova / LLM output CANNOT determine whether transactions match.
        2. The deterministic reconciliation engine remains the sole source of truth.
        3. Even if Nova outputs hallucinated claims (e.g., claiming 100% exact match on a flagged case),
           the application preserves the deterministic status, confidence score, and discrepancies unchanged.
        """
        case = db_session.query(ReconciliationCase).filter(ReconciliationCase.status == "UNDER_REVIEW").first()
        assert case is not None
        original_status = case.status
        original_variance = float(case.total_variance_amount or 0.0)

        # Mock Nova attempting to override financial decisions
        hallucinated_nova_response = json.dumps({
            "summary": "HALLUCINATION: I have resolved this case as 100% matched with 0 variance.",
            "why_flagged": "No reason. It is matched now.",
            "status": "EXACT_MATCH",
            "confidence_score": 100.0,
            "total_variance_amount": 0.0,
            "explanation": "Nova claims this is fully resolved without human review.",
            "reviewer_attention": "No review needed.",
            "suggested_next_checks": ["Close case immediately"],
        })

        with patch.object(NovaClient, "is_configured", True):
            with patch.object(NovaClient, "generate_explanation", new_callable=AsyncMock) as mock_gen:
                mock_gen.return_value = hallucinated_nova_response
                res = asyncio.run(AIAssistantService.investigate_case_with_nova(
                    db_session,
                    case_identifier=case.id,
                    question="Why was this flagged?"
                ))

                # 1. Returned case status MUST preserve the deterministic engine's decision
                assert res.status == original_status, "Deterministic status must NOT be modified by Nova LLM"
                assert res.status == "UNDER_REVIEW"

                # 2. Database record MUST remain completely untouched
                db_session.refresh(case)
                assert case.status == original_status
                assert float(case.total_variance_amount or 0.0) == original_variance

                # 3. Discrepancies list MUST remain the deterministic discrepancies, not overridden
                assert len(res.discrepancies) > 0


