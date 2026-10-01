from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models import (
    DataSource,
    Entity,
    Transaction,
    Invoice,
    CryptoTransaction,
    ReconciliationCase,
    ReconciliationMatch,
    DiscrepancyRecord,
)
from app.services.reconciliation.models import (
    MatchAlgorithmPass,
    MatchStatus,
    DiscrepancyType,
    ReconciliationRunRequest,
)
from app.services.reconciliation.engine import ReconciliationEngine
from app.services.reconciliation.service import ReconciliationService

client = TestClient(app)


class MockRecord:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestReconciliationEnginePasses:
    """Test unit execution of each reconciliation pass in the deterministic engine"""

    def test_pass_1_exact_match(self):
        bank_txn = MockRecord(
            id="b-1",
            source_type="BANK",
            transaction_id="TXN-BANK-001",
            amount=Decimal("50000.00"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            payment_reference="REF-EXACT-99",
            reference_order_id="ORD-101",
        )
        gateway_txn = MockRecord(
            id="g-1",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-GATEWAY-001",
            amount=Decimal("50000.00"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            payment_reference="REF-EXACT-99",
            reference_order_id="ORD-101",
            fee_amount=Decimal("0.0"),
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[bank_txn, gateway_txn],
            invoices=[],
            crypto_transactions=[],
        )

        assert len(results) == 1
        m = results[0]
        assert m.algorithm_pass == MatchAlgorithmPass.PASS_1_EXACT
        assert m.match_status == MatchStatus.EXACT_MATCH
        assert m.confidence_score == 100.0
        assert len(m.discrepancies) == 0
        assert len(m.evidence) > 0

    def test_pass_2_settlement_date_lag(self):
        bank_txn = MockRecord(
            id="b-lag",
            source_type="BANK",
            transaction_id="TXN-BANK-LAG",
            amount=Decimal("25000.00"),
            currency="USD",
            transaction_date=date(2026, 9, 29),  # T+2
            payment_reference="REF-LAG-22",
        )
        gateway_txn = MockRecord(
            id="g-lag",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-GATEWAY-LAG",
            amount=Decimal("25000.00"),
            currency="USD",
            transaction_date=date(2026, 9, 27),
            payment_reference="REF-LAG-22",
            fee_amount=Decimal("0.0"),
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[bank_txn, gateway_txn],
            invoices=[],
            crypto_transactions=[],
            date_tolerance_days=3,
        )

        assert len(results) == 1
        m = results[0]
        assert m.algorithm_pass == MatchAlgorithmPass.PASS_2_ID_CORRELATION
        assert m.confidence_score >= 90.0
        assert len(m.discrepancies) == 1
        disc = m.discrepancies[0]
        assert disc.discrepancy_type == DiscrepancyType.DATE
        assert disc.root_cause_category == "T_PLUS_LAG"
        assert disc.difference_numeric == 2.0

    def test_pass_3_gateway_fee_netting(self):
        # Gross $1,250 - $37.50 fee = Net $1,212.50 deposited in Bank
        bank_txn = MockRecord(
            id="b-fee",
            source_type="BANK",
            transaction_id="TXN-BANK-NET",
            amount=Decimal("1212.50"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            payment_reference="PAY-NET-01",
        )
        gateway_txn = MockRecord(
            id="g-fee",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-GATEWAY-GROSS",
            amount=Decimal("1250.00"),
            fee_amount=Decimal("37.50"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            payment_reference="PAY-NET-01",
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[bank_txn, gateway_txn],
            invoices=[],
            crypto_transactions=[],
        )

        assert len(results) == 1
        m = results[0]
        assert m.algorithm_pass == MatchAlgorithmPass.PASS_3_FEE_NETTING
        assert m.confidence_score >= 90.0
        assert any(d.root_cause_category == "PROCESSING_FEE" for d in m.discrepancies)
        fee_disc = next(d for d in m.discrepancies if d.root_cause_category == "PROCESSING_FEE")
        assert fee_disc.difference_numeric == 37.50

    def test_pass_4_crypto_invoice_reconciliation(self):
        crypto_txn = MockRecord(
            id="c-1",
            tx_hash="0x3a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
            blockchain="ETHEREUM",
            amount=Decimal("5000.00"),
            amount_usd=Decimal("5000.00"),
            token_symbol="USDT",
            memo="Payment for INV-2026-909",
        )
        inv = MockRecord(
            id="inv-909",
            invoice_number="INV-2026-909",
            total_amount=Decimal("5000.00"),
            currency="USD",
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[],
            invoices=[inv],
            crypto_transactions=[crypto_txn],
        )

        assert len(results) == 1
        m = results[0]
        assert m.algorithm_pass == MatchAlgorithmPass.PASS_4_CRYPTO_ON_CHAIN
        assert m.match_type == "CRYPTO_TO_INVOICE"
        assert m.confidence_score >= 90.0

    def test_pass_6_duplicate_detection(self):
        t1 = MockRecord(
            id="dup-1",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-DUP-A",
            amount=Decimal("499.00"),
            currency="USD",
            payment_reference="ORDER-DUP-888",
        )
        t2 = MockRecord(
            id="dup-2",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-DUP-B",
            amount=Decimal("499.00"),
            currency="USD",
            payment_reference="ORDER-DUP-888",
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[t1, t2],
            invoices=[],
            crypto_transactions=[],
        )

        assert any(r.match_status == MatchStatus.DUPLICATE for r in results)
        dup_match = next(r for r in results if r.match_status == MatchStatus.DUPLICATE)
        assert dup_match.algorithm_pass == MatchAlgorithmPass.PASS_6_DUPLICATE_DETECTION
        assert any(d.discrepancy_type == DiscrepancyType.DUPLICATE_ENTRY for d in dup_match.discrepancies)

    def test_pass_7_orphan_unrecorded_fee(self):
        fee_txn = MockRecord(
            id="orphan-1",
            source_type="BANK",
            transaction_id="TXN-BANK-WIRE-FEE",
            amount=Decimal("120.00"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            description="Monthly international outgoing wire service fee",
            status="SETTLED",
            payment_reference="WIRE-FEE-120",
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[fee_txn],
            invoices=[],
            crypto_transactions=[],
        )

        assert len(results) == 1
        m = results[0]
        assert m.algorithm_pass == MatchAlgorithmPass.PASS_7_ORPHAN_EXCEPTION
        assert m.match_status == MatchStatus.MISSING_RECORD
        assert len(m.discrepancies) == 1
        assert m.discrepancies[0].discrepancy_type == DiscrepancyType.MISSING_ENTRY
        assert m.discrepancies[0].root_cause_category == "UNRECORDED_EXPENSE"

    def test_currency_mismatch_prevents_false_matches(self):
        bank_jpy = MockRecord(
            id="b-jpy",
            source_type="BANK",
            transaction_id="TXN-JPY",
            amount=Decimal("50000.00"),
            currency="JPY",
            transaction_date=date(2026, 9, 29),
            payment_reference="REF-CROSS-01",
            counterparty_normalized_name="Acme Global",
        )
        gw_usd = MockRecord(
            id="g-usd",
            source_type="PAYMENT_GATEWAY",
            transaction_id="TXN-USD",
            amount=Decimal("50000.00"),
            currency="USD",
            transaction_date=date(2026, 9, 29),
            payment_reference="REF-CROSS-01",
            counterparty_normalized_name="Acme Global",
            fee_amount=Decimal("0.0"),
        )

        results = ReconciliationEngine.run_multi_pass_reconciliation(
            transactions=[bank_jpy, gw_usd],
            invoices=[],
            crypto_transactions=[],
        )

        # Must NOT match because JPY != USD
        exact_or_partial = [r for r in results if r.match_status in (MatchStatus.EXACT_MATCH, MatchStatus.PARTIAL_MATCH)]
        assert len(exact_or_partial) == 0


class TestReconciliationServiceAndDatabase:
    """Test full database reconciliation execution, persistence, and querying"""

    def test_service_execute_reconciliation(self):
        db = SessionLocal()
        try:
            req = ReconciliationRunRequest(
                case_title="Full Test Reconciliation Run",
                amount_tolerance=0.05,
                date_tolerance_days=3,
            )
            summary = ReconciliationService.execute_reconciliation(db=db, req=req)

            assert summary.case_id is not None
            assert summary.case_number.startswith("CASE-")
            assert summary.total_records_processed > 0
            assert (summary.exact_matches_count + summary.partial_matches_count) > 0
            assert summary.match_rate_percentage > 0.0

            # Verify case persisted in database
            case_orm = db.query(ReconciliationCase).filter(ReconciliationCase.id == summary.case_id).first()
            assert case_orm is not None
            assert len(case_orm.matches) > 0
        finally:
            if "summary" in locals() and summary and summary.case_id:
                db.query(DiscrepancyRecord).filter(DiscrepancyRecord.case_id == summary.case_id).delete()
                db.query(ReconciliationMatch).filter(ReconciliationMatch.case_id == summary.case_id).delete()
                db.query(ReconciliationCase).filter(ReconciliationCase.id == summary.case_id).delete()
                db.commit()
            db.close()


class TestReconciliationAPIEndpoints:
    """Test REST API endpoints for reconciliation runs, cases, and reviews"""

    def test_api_trigger_and_query_case(self):
        # 1. Trigger reconciliation run
        payload = {
            "case_title": "Automated API Reconciliation Run",
            "amount_tolerance": 0.05,
            "date_tolerance_days": 3,
        }
        run_resp = client.post("/api/v1/reconciliation/run", json=payload)
        assert run_resp.status_code == 201
        run_data = run_resp.json()
        case_id = run_data["case_id"]
        assert "exact_matches_count" in run_data
        assert "match_rate_percentage" in run_data

        # 2. Get case list
        list_resp = client.get("/api/v1/reconciliation/cases")
        assert list_resp.status_code == 200
        cases = list_resp.json()
        assert len(cases) > 0
        assert any(c["id"] == case_id for c in cases)

        # 3. Get case detail
        detail_resp = client.get(f"/api/v1/reconciliation/cases/{case_id}")
        assert detail_resp.status_code == 200
        case_detail = detail_resp.json()
        assert case_detail["id"] == case_id
        assert "matches" in case_detail
        assert "discrepancies" in case_detail

        # 4. Review a match if present
        if len(case_detail["matches"]) > 0:
            first_match = case_detail["matches"][0]
            match_id = first_match["id"]

            review_payload = {
                "reviewer_name": "Audit Officer Sarah",
                "action": "CONFIRM_MATCH",
                "notes": "Verified against gateway webhook logs.",
            }
            review_resp = client.post(f"/api/v1/reconciliation/matches/{match_id}/review", json=review_payload)
            assert review_resp.status_code == 200
            review_data = review_resp.json()
            assert review_data["reviewer"] == "Audit Officer Sarah"
            assert review_data["new_status"] == "EXACT_MATCH"

        # Cleanup test case
        db = SessionLocal()
        try:
            if "match_id" in locals():
                from app.models.manual_review import ManualReview
                db.query(ManualReview).filter(ManualReview.match_id == match_id).delete()
            db.query(DiscrepancyRecord).filter(DiscrepancyRecord.case_id == case_id).delete()
            db.query(ReconciliationMatch).filter(ReconciliationMatch.case_id == case_id).delete()
            db.query(ReconciliationCase).filter(ReconciliationCase.id == case_id).delete()
            db.commit()
        finally:
            db.close()

    def test_api_list_matches(self):
        matches_resp = client.get("/api/v1/reconciliation/matches?limit=10")
        assert matches_resp.status_code == 200
        matches = matches_resp.json()
        assert isinstance(matches, list)
        if len(matches) > 0:
            assert "confidence_score" in matches[0]
            assert "algorithm_pass" in matches[0]
