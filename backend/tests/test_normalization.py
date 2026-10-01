import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.normalization.normalizer import NormalizationEngine

client = TestClient(app)


class TestFieldNormalization:
    """Test suite for individual field normalizations in NormalizationEngine"""

    def test_name_normalization(self):
        # Honorific removal & title casing
        res = NormalizationEngine.normalize_name("dr. john doe")
        assert res.is_valid is True
        assert res.normalized_value == "John Doe"
        assert res.original_value == "dr. john doe"

        # "Last, First" reversal
        res_rev = NormalizationEngine.normalize_name("Smith, Jane")
        assert res_rev.normalized_value == "Jane Smith"

        # Empty string handling
        res_empty = NormalizationEngine.normalize_name("")
        assert res_empty.is_valid is False

    def test_company_name_normalization(self):
        # ABC LTD, ABC Limited, ABC LIMITED. -> "abc ltd"
        cases = ["ABC LTD", "ABC Limited", "ABC LIMITED.", "abc ltd."]
        for case in cases:
            res = NormalizationEngine.normalize_company_name(case)
            assert res.is_valid is True
            assert res.normalized_value == "abc ltd", f"Failed for {case}: got {res.normalized_value}"

        # Acme Corp. -> "acme corp"
        res_corp = NormalizationEngine.normalize_company_name("Acme Corp.")
        assert res_corp.normalized_value == "acme corp"

        # Global Solutions LLC -> "global solutions llc"
        res_llc = NormalizationEngine.normalize_company_name("Global Solutions L.L.C.")
        assert res_llc.normalized_value == "global solutions llc"

    def test_wallet_address_normalization(self):
        # EVM address lowercasing
        evm_checksum = "0x71C63739a7E57930059869E032b85538f41A332e"
        res = NormalizationEngine.normalize_wallet_address(evm_checksum)
        assert res.is_valid is True
        assert res.normalized_value == evm_checksum.lower()
        assert res.metadata.get("network_type") == "EVM"

        # Solana Base58 format
        sol_addr = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        res_sol = NormalizationEngine.normalize_wallet_address(sol_addr)
        assert res_sol.is_valid is True
        assert res_sol.normalized_value == sol_addr

        # Invalid wallet string
        res_inv = NormalizationEngine.normalize_wallet_address("0xnot-a-valid-address")
        assert res_inv.is_valid is False

    def test_transaction_id_normalization(self):
        res = NormalizationEngine.normalize_transaction_id(" #TXN_2026/0998 ")
        assert res.is_valid is True
        assert res.normalized_value == "TXN-2026-0998"
        assert res.original_value == " #TXN_2026/0998 "

    def test_invoice_id_normalization(self):
        cases = [
            ("Invoice: 2026-001", "INV-2026-001"),
            ("Inv #1044", "INV-1044"),
            ("INV-2026-88", "INV-2026-88"),
            ("10029", "INV-10029"),
        ]
        for raw, expected in cases:
            res = NormalizationEngine.normalize_invoice_id(raw)
            assert res.is_valid is True
            assert res.normalized_value == expected

    def test_amount_normalization(self):
        # Standard Dollar amount
        res_usd = NormalizationEngine.normalize_amount("$50,000.00")
        assert res_usd.is_valid is True
        assert res_usd.normalized_value == 50000.0
        assert res_usd.metadata.get("direction") == "CREDIT"

        # Indian Rupee symbol
        res_inr = NormalizationEngine.normalize_amount("₹50,000")
        assert res_inr.is_valid is True
        assert res_inr.normalized_value == 50000.0

        # European decimal notation: 49.500,00
        res_eur = NormalizationEngine.normalize_amount("€ 49.500,00")
        assert res_eur.is_valid is True
        assert res_eur.normalized_value == 49500.0

        # Parenthetical negative amount: (5,000.00)
        res_neg = NormalizationEngine.normalize_amount("(5,000.00)")
        assert res_neg.is_valid is True
        assert res_neg.normalized_value == 5000.0
        assert res_neg.metadata.get("direction") == "DEBIT"

    def test_currency_normalization(self):
        symbols = [
            ("$", "USD"),
            ("₹", "INR"),
            ("€", "EUR"),
            ("£", "GBP"),
            ("usdt", "USDT"),
            ("eth", "ETH"),
            ("sol", "SOL"),
            ("EUR", "EUR"),
        ]
        for sym, expected in symbols:
            res = NormalizationEngine.normalize_currency(sym)
            assert res.is_valid is True
            assert res.normalized_value == expected

    def test_date_normalization(self):
        cases = [
            ("29/09/2026", "2026-09-29"),
            ("2026-09-29", "2026-09-29"),
            ("09-29-2026", "2026-09-29"),
            ("29-Sep-2026", "2026-09-29"),
            ("Sep 29, 2026", "2026-09-29"),
        ]
        for raw, expected in cases:
            res = NormalizationEngine.normalize_date(raw)
            assert res.is_valid is True
            assert res.normalized_value == expected, f"Failed for {raw}: got {res.normalized_value}"

    def test_timestamp_normalization(self):
        # Epoch seconds (1790680800 = 2026-09-29T11:20:00Z)
        res_epoch = NormalizationEngine.normalize_timestamp(1790680800)
        assert res_epoch.is_valid is True
        assert "2026" in res_epoch.normalized_value
        assert res_epoch.normalized_value.endswith("Z")

        # ISO string with space
        res_iso = NormalizationEngine.normalize_timestamp("2026-09-29 14:30:00")
        assert res_iso.is_valid is True
        assert res_iso.normalized_value == "2026-09-29T14:30:00Z"

    def test_payment_reference_normalization(self):
        cases = [
            ("Ref: UTR-998234", "UTR-998234"),
            ("Check #1044", "1044"),
            ("UTR: HDFC-992-001", "HDFC-992-001"),
        ]
        for raw, expected in cases:
            res = NormalizationEngine.normalize_payment_reference(raw)
            assert res.is_valid is True
            assert res.normalized_value == expected


class TestRecordNormalization:
    """Test full row/record normalization preserving original values"""

    def test_full_record_normalization(self):
        raw_row = {
            "counterparty": "Acme Global Ltd.",
            "amount": "$49,500.00",
            "currency": "$",
            "date": "29/09/2026",
            "transaction_id": "#TXN-001/88",
            "payment_reference": "Ref: UTR-776655",
            "custom_tag": "Monthly Subscription",
        }
        normalized_rec = NormalizationEngine.normalize_record(raw_row, record_type="TRANSACTION")

        assert normalized_rec.all_valid is True
        assert normalized_rec.record_type == "TRANSACTION"

        # Check preserved original values
        assert normalized_rec.get_original("counterparty") == "Acme Global Ltd."
        assert normalized_rec.get_original("amount") == "$49,500.00"
        assert normalized_rec.get_original("transaction_id") == "#TXN-001/88"

        # Check normalized canonical values
        assert normalized_rec.get_normalized("counterparty") == "acme global ltd"
        assert normalized_rec.get_normalized("amount") == 49500.0
        assert normalized_rec.get_normalized("currency") == "USD"
        assert normalized_rec.get_normalized("transaction_date") == "2026-09-29"
        assert normalized_rec.get_normalized("transaction_id") == "TXN-001-88"
        assert normalized_rec.get_normalized("payment_reference") == "UTR-776655"
        assert normalized_rec.get_normalized("custom_tag") == "Monthly Subscription"


class TestNormalizationAPIEndpoints:
    """Test REST API endpoints for normalization"""

    def test_api_normalize_field(self):
        payload = {"field_type": "company_name", "value": "Acme Technologies Limited"}
        response = client.post("/api/v1/normalization/field", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["original_value"] == "Acme Technologies Limited"
        assert data["normalized_value"] == "acme technologies ltd"
        assert data["is_valid"] is True

    def test_api_normalize_record(self):
        payload = {
            "record": {
                "counterparty": "Stripe Payments Ltd",
                "amount": "€ 1,250.50",
                "currency": "€",
                "date": "29-Sep-2026",
            },
            "record_type": "TRANSACTION",
        }
        response = client.post("/api/v1/normalization/record", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["all_valid"] is True
        fields = data["fields"]
        assert fields["counterparty"]["normalized_value"] == "stripe payments ltd"
        assert fields["amount"]["normalized_value"] == 1250.5
        assert fields["currency"]["normalized_value"] == "EUR"
        assert fields["transaction_date"]["normalized_value"] == "2026-09-29"

    def test_api_normalize_batch(self):
        payload = {
            "records": [
                {"counterparty": "Alpha LLC", "amount": "$100.00"},
                {"counterparty": "Beta Inc", "amount": "$200.00"},
            ],
            "record_type": "TRANSACTION",
        }
        response = client.post("/api/v1/normalization/batch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total_records"] == 2
        assert data["total_valid"] == 2
        assert data["valid_percentage"] == 100.0
