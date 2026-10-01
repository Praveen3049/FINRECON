import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
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

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.core.database import get_db

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()


def test_seed_database_execution(db_session):
    """Verifies that seed_database populates all 10 tables cleanly."""
    summary = seed_database(db_session)
    assert summary["data_sources"] == 5
    assert summary["entities"] == 4
    assert summary["transactions"] >= 8
    assert summary["invoices"] >= 3
    assert summary["crypto_transactions"] >= 3
    assert summary["reconciliation_cases"] >= 8
    assert summary["reconciliation_matches"] >= 8
    assert summary["discrepancy_records"] >= 5
    assert summary["manual_reviews"] >= 1
    assert summary["audit_logs"] >= 3


def test_exact_matches_demonstrated(db_session):
    """Verifies exact matches exist in the database."""
    exact_matches = db_session.query(ReconciliationMatch).filter_by(match_status="EXACT_MATCH").all()
    assert len(exact_matches) >= 3  # Standard exact, Crypto-to-invoice, Crypto-to-ERP
    for m in exact_matches:
        assert m.confidence_score >= 95.0
        assert m.confidence_level == "HIGH"


def test_partial_matches_and_discrepancies(db_session):
    """Verifies partial matches with amount & date discrepancies."""
    partial_matches = db_session.query(ReconciliationMatch).filter_by(match_status="PARTIAL_MATCH").all()
    assert len(partial_matches) >= 2

    # Amount discrepancy
    amount_disc = db_session.query(DiscrepancyRecord).filter_by(discrepancy_type="AMOUNT").first()
    assert amount_disc is not None
    assert amount_disc.difference_numeric is not None
    assert amount_disc.root_cause_category in ["PROCESSING_FEE", "FX_RATE_SHIFT"]

    # Date discrepancy
    date_disc = db_session.query(DiscrepancyRecord).filter_by(discrepancy_type="DATE").first()
    assert date_disc is not None
    assert date_disc.root_cause_category == "T_PLUS_LAG"


def test_duplicate_detection_scenario(db_session):
    """Verifies duplicate transaction pairs are recorded."""
    dup_match = db_session.query(ReconciliationMatch).filter_by(match_status="DUPLICATE").first()
    assert dup_match is not None
    assert dup_match.confidence_score >= 98.0
    
    dup_disc = db_session.query(DiscrepancyRecord).filter_by(discrepancy_type="DUPLICATE_ENTRY").first()
    assert dup_disc is not None
    assert dup_disc.severity == "CRITICAL"


def test_missing_record_scenario(db_session):
    """Verifies orphaned bank record without accounting counterpart."""
    missing_match = db_session.query(ReconciliationMatch).filter_by(match_status="MISSING_RECORD").first()
    assert missing_match is not None
    assert missing_match.matched_transaction_id is None

    missing_disc = db_session.query(DiscrepancyRecord).filter_by(discrepancy_type="MISSING_ENTRY").first()
    assert missing_disc is not None
    assert missing_disc.root_cause_category == "UNRECORDED_EXPENSE"


def test_conflicting_record_scenario(db_session):
    """Verifies conflicting entities with identical order references."""
    conflict_match = db_session.query(ReconciliationMatch).filter_by(match_status="CONFLICTING_RECORD").first()
    assert conflict_match is not None

    conflict_disc = db_session.query(DiscrepancyRecord).filter_by(discrepancy_type="ENTITY").first()
    assert conflict_disc is not None
    assert conflict_disc.source_value != conflict_disc.matched_value


def test_crypto_reconciliation_records(db_session):
    """Verifies crypto transactions linked to invoices and ERP journal entries."""
    crypto_txs = db_session.query(CryptoTransaction).all()
    assert len(crypto_txs) >= 3

    networks = {tx.blockchain_network for tx in crypto_txs}
    assert "ETHEREUM" in networks
    assert "POLYGON" in networks

    assets = {tx.asset for tx in crypto_txs}
    assert "USDT" in assets
    assert "USDC" in assets
    assert "ETH" in assets

    # Crypto-to-invoice match
    crypto_inv_match = db_session.query(ReconciliationMatch).filter_by(match_type="CRYPTO_TO_INVOICE").first()
    assert crypto_inv_match is not None
    assert crypto_inv_match.crypto_transaction_id is not None
    assert crypto_inv_match.invoice_id is not None


def test_api_database_summary_endpoint(db_session):
    """Verifies the /api/v1/database-summary endpoint."""
    response = client.get("/api/v1/database-summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_tables"] == 10
    assert data["table_counts"]["data_sources"] == 5
    assert data["table_counts"]["crypto_transactions"] >= 3
    assert len(data["recent_cases"]) > 0
