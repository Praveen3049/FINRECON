import io
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_bank_statement_ingestion():
    csv_content = (
        "Transaction ID,Date,Description,Amount,Currency,Balance,Reference\n"
        "TXN-BANK-T001,2026-09-20,Wire Transfer In,5000.00,USD,25000.00,REF-T101\n"
        "TXN-BANK-T002,2026-09-21,Client Settlement,12500.50,USD,37500.50,REF-T102\n"
        "TXN-BANK-T003,2026-09-22,ACH Payment,3400.00,USD,40900.50,REF-T103\n"
        "TXN-BANK-T004,2026-09-23,Vendor Transfer,850.00,USD,41750.50,REF-T104\n"
    ).encode("utf-8")
    
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("bank_statement_sample.csv", io.BytesIO(csv_content), "text/csv")},
        data={"source_type": "BANK", "source_name": "Test Bank Feed In-Memory"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert summary["source_type"] == "BANK"
    assert summary["total_records"] == 4
    assert summary["processed_records"] == 4
    assert summary["failed_records"] == 0
    assert len(summary["preview"]) > 0


def test_payment_gateway_ingestion():
    gateway_data = [
        {"transaction_id": "GW-T001", "created_at": "2026-09-20T10:00:00Z", "amount": 5000.00, "fee": 15.00, "currency": "USD", "status": "succeeded", "order_id": "ORD-T101", "payment_reference": "REF-T101"},
        {"transaction_id": "GW-T002", "created_at": "2026-09-21T11:00:00Z", "amount": 12500.50, "fee": 37.50, "currency": "USD", "status": "succeeded", "order_id": "ORD-T102", "payment_reference": "REF-T102"}
    ]
    json_bytes = json.dumps(gateway_data).encode("utf-8")
    
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("payment_gateway_sample.json", io.BytesIO(json_bytes), "application/json")},
        data={"source_type": "PAYMENT_GATEWAY", "source_name": "Test Stripe Feed In-Memory"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert summary["source_type"] == "PAYMENT_GATEWAY"
    assert summary["total_records"] == 2
    assert summary["processed_records"] == 2


def test_crypto_transactions_ingestion():
    crypto_data = [
        {"tx_hash": "0xabc1230000000000000000000000000000000000000000000000000000000001", "network": "ETHEREUM", "from": "0x1111111111111111111111111111111111111111", "to": "0x2222222222222222222222222222222222222222", "asset": "USDT", "token_amount": 5000, "fiat_value": 5000, "fiat_currency": "USD", "timestamp": "2026-09-20T12:00:00Z", "confirmation_status": "CONFIRMED"},
        {"tx_hash": "0xabc1230000000000000000000000000000000000000000000000000000000002", "network": "POLYGON", "from": "0x3333333333333333333333333333333333333333", "to": "0x4444444444444444444444444444444444444444", "asset": "USDC", "token_amount": 3400, "fiat_value": 3400, "fiat_currency": "USD", "timestamp": "2026-09-21T14:00:00Z", "confirmation_status": "CONFIRMED"}
    ]
    json_bytes = json.dumps(crypto_data).encode("utf-8")
    
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("crypto_transactions_sample.json", io.BytesIO(json_bytes), "application/json")},
        data={"source_type": "CRYPTO", "source_name": "Test Crypto Feed In-Memory"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert summary["source_type"] == "CRYPTO"
    assert summary["total_records"] == 2
    assert summary["processed_records"] + summary["failed_records"] == summary["total_records"]


def test_invoices_ingestion():
    csv_content = (
        "Invoice Number,Issue Date,Due Date,Entity Name,Subtotal,Tax,Total Amount,Currency,Status\n"
        "INV-TEST-001,2026-09-15,2026-09-30,Acme Global,4500.00,500.00,5000.00,USD,ISSUED\n"
        "INV-TEST-002,2026-09-18,2026-10-02,Beta Labs,11500.00,1000.50,12500.50,USD,ISSUED\n"
    ).encode("utf-8")
    
    response = client.post(
        "/api/v1/ingestion/upload",
        files={"file": ("invoices_sample.csv", io.BytesIO(csv_content), "text/csv")},
        data={"source_type": "INVOICE", "source_name": "Test Invoice Feed In-Memory"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    summary = data["summary"]
    assert summary["source_type"] == "INVOICE"
    assert summary["total_records"] == 2


def test_sample_download_endpoints():
    sources = ["BANK", "PAYMENT_GATEWAY", "ACCOUNTING", "INVOICE", "CRYPTO"]
    for src in sources:
        response = client.get(f"/api/v1/ingestion/sample/{src}")
        assert response.status_code == 200, f"Sample download for {src} should return 200"


def test_list_sources_endpoint():
    response = client.get("/api/v1/ingestion/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4


def test_create_and_manage_accounts():
    # 1. Create account
    res = client.post(
        "/api/v1/ingestion/accounts",
        json={
            "name": "Test HDFC Operating Account",
            "source_type": "BANK",
            "account_identifier": "HDFC-TEST-9901",
            "currency": "INR",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    acc = data["account"]
    assert acc["name"] == "Test HDFC Operating Account"
    assert acc["currency"] == "INR"
    acc_id = acc["id"]

    # 2. List accounts
    list_res = client.get("/api/v1/ingestion/accounts")
    assert list_res.status_code == 200
    accs = list_res.json()
    assert any(a["id"] == acc_id for a in accs)

    # 3. Delete account
    del_res = client.delete(f"/api/v1/ingestion/accounts/{acc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"
