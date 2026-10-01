import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.services.crypto.models import BlockExplorerHelper
from app.services.crypto.service import CryptoReconciliationService

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_crypto_test_data():
    db = SessionLocal()
    from app.models import DataSource, CryptoTransaction
    from decimal import Decimal
    from datetime import datetime, timezone
    import uuid

    # Ensure crypto datasource exists
    src = db.query(DataSource).filter(DataSource.source_type == "CRYPTO").first()
    created_src = False
    if not src:
        src = DataSource(
            id="test_crypto_source_id",
            name="Test Crypto Treasury Feed",
            source_type="CRYPTO",
            file_format="JSON",
            account_identifier="0x29D7d1dd5B6f9C864d9db560D72a247c178a836B",
            currency="USD",
            is_active=True,
        )
        db.add(src)
        created_src = True

    created_txns = []
    if db.query(CryptoTransaction).count() == 0:
        tx1 = CryptoTransaction(
            id=str(uuid.uuid4()),
            source_id=src.id,
            blockchain_network="ETHEREUM",
            transaction_hash="0x4a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b",
            wallet_from="0x71C80915E33366b90c485657519EF4e1",
            wallet_to="0x29D7d1dd5B6f9C864d9db560D72a247c178a836B",
            asset="ETH",
            token_amount=Decimal("1.5"),
            fiat_value=Decimal("3675.00"),
            fiat_currency="USD",
            gas_fee=Decimal("0.002"),
            gas_fee_fiat=Decimal("4.90"),
            block_number=19482910,
            confirmation_status="CONFIRMED",
            transaction_timestamp=datetime.now(timezone.utc),
        )
        db.add(tx1)
        created_txns.append(tx1.id)
    db.commit()

    try:
        yield
    finally:
        if created_txns:
            db.query(CryptoTransaction).filter(CryptoTransaction.id.in_(created_txns)).delete(synchronize_session=False)
        if created_src:
            db.query(DataSource).filter(DataSource.id == "test_crypto_source_id").delete(synchronize_session=False)
        db.commit()
        db.close()


class TestCryptoCalculations:
    """Test unit execution of gas fee calculations, slippage tolerances, and explorer links"""

    def test_gas_fee_calculation(self):
        # 21,000 gas units * 30 Gwei * 1e-9 = 0.00063 ETH * $2,450 = $1.5435 USD
        calc = CryptoReconciliationService.calculate_gas_fee(
            network="ETHEREUM",
            gas_units=21000,
            gas_price_gwei=30.0,
            native_usd_price=2450.0,
        )
        assert calc.native_token == "ETH"
        assert abs(calc.gas_fee_native - 0.00063) < 1e-7
        assert abs(calc.gas_fee_usd - 1.5435) < 1e-3

    def test_polygon_gas_fee_calculation(self):
        calc = CryptoReconciliationService.calculate_gas_fee(
            network="POLYGON",
            gas_units=50000,
            gas_price_gwei=40.0,
            native_usd_price=0.42,
        )
        assert calc.native_token == "MATIC"
        assert calc.gas_fee_usd > 0.0

    def test_slippage_analysis_acceptable(self):
        # $5,000 expected vs $4,990 actual -> 0.20% slippage (within 0.5% tolerance)
        analysis = CryptoReconciliationService.calculate_slippage(
            expected_fiat_amount=5000.0,
            actual_fiat_amount=4990.0,
            tolerance_percentage=0.5,
        )
        assert analysis.is_acceptable is True
        assert abs(analysis.slippage_percentage - 0.20) < 0.01
        assert analysis.slippage_usd == -10.0

    def test_slippage_analysis_unacceptable(self):
        # $5,000 expected vs $4,900 actual -> 2.0% slippage (exceeds 0.5% tolerance)
        analysis = CryptoReconciliationService.calculate_slippage(
            expected_fiat_amount=5000.0,
            actual_fiat_amount=4900.0,
            tolerance_percentage=0.5,
        )
        assert analysis.is_acceptable is False
        assert abs(analysis.slippage_percentage - 2.0) < 0.01

    def test_block_explorer_helpers(self):
        tx_hash = "0x71c8364437a9c47f65630c45159392c1a5641001002003004005006007008009"
        eth_url = BlockExplorerHelper.get_tx_url("ETHEREUM", tx_hash)
        assert "etherscan.io/tx/" in eth_url
        assert tx_hash in eth_url

        poly_url = BlockExplorerHelper.get_tx_url("POLYGON", tx_hash)
        assert "polygonscan.com/tx/" in poly_url

        sol_url = BlockExplorerHelper.get_tx_url("SOLANA", "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d")
        assert "solscan.io/tx/" in sol_url


class TestCryptoServiceDatabase:
    """Test database queries for enriched on-chain transactions, treasury wallets, and analytics"""

    def test_get_enriched_transactions(self):
        db = SessionLocal()
        try:
            txns = CryptoReconciliationService.get_enriched_transactions(db=db, limit=10)
            assert len(txns) > 0
            first = txns[0]
            assert "transaction_hash" in first
            assert "explorer_urls" in first
            assert "tx" in first["explorer_urls"]
            assert "reconciliation_status" in first
            assert "fiat_value" in first
        finally:
            db.close()

    def test_get_treasury_wallets(self):
        db = SessionLocal()
        try:
            wallets = CryptoReconciliationService.get_treasury_wallets(db=db)
            assert isinstance(wallets, list)
            assert len(wallets) > 0
            first = wallets[0]
            assert "wallet_address" in first
            assert "network" in first
            assert "token_balances" in first
            assert "explorer_url" in first
        finally:
            db.close()

    def test_get_network_analytics(self):
        db = SessionLocal()
        try:
            analytics = CryptoReconciliationService.get_network_analytics(db=db)
            assert "total_crypto_transactions" in analytics
            assert analytics["total_crypto_transactions"] > 0
            assert "total_fiat_volume_usd" in analytics
            assert "networks" in analytics
            assert "ETHEREUM" in analytics["networks"]
        finally:
            db.close()


class TestCryptoAPIEndpoints:
    """Test REST API endpoints for crypto reconciliation"""

    def test_api_list_transactions(self):
        res = client.get("/api/v1/crypto/transactions?limit=5")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "explorer_urls" in data[0]

    def test_api_list_wallets(self):
        res = client.get("/api/v1/crypto/wallets")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_api_analytics(self):
        res = client.get("/api/v1/crypto/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "total_fiat_volume_usd" in data
        assert "networks" in data

    def test_api_verify_hash(self):
        payload = {
            "blockchain_network": "ETHEREUM",
            "transaction_hash": "0x3a9b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
        }
        res = client.post("/api/v1/crypto/verify-hash", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid_format"] is True
        assert "etherscan.io/tx/" in data["explorer_url"]

    def test_api_calculate_gas(self):
        payload = {
            "blockchain_network": "ETHEREUM",
            "gas_units": 21000,
            "gas_price_gwei": 30.0,
            "native_usd_price": 2500.0,
        }
        res = client.post("/api/v1/crypto/calculate-gas", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["native_token"] == "ETH"
        assert data["gas_fee_usd"] > 0

    def test_api_slippage_analysis(self):
        payload = {
            "expected_fiat_amount": 10000.0,
            "actual_fiat_amount": 9980.0,
            "tolerance_percentage": 0.5,
        }
        res = client.post("/api/v1/crypto/slippage-analysis", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["is_acceptable"] is True
        assert data["slippage_percentage"] == 0.2
