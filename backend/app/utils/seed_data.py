from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import json
import uuid
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.logging import logger
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


def seed_database(db: Session) -> dict:
    logger.info("Starting FinRecon database seeding...")
    
    # 0. Clean existing data in dependency order
    db.query(AuditLog).delete()
    db.query(ManualReview).delete()
    db.query(DiscrepancyRecord).delete()
    db.query(ReconciliationMatch).delete()
    db.query(ReconciliationCase).delete()
    db.query(CryptoTransaction).delete()
    db.query(Invoice).delete()
    db.query(Transaction).delete()
    db.query(Entity).delete()
    db.query(DataSource).delete()
    db.commit()

    # 1. Create Data Sources (5 Core Sources)
    src_bank = DataSource(
        id=str(uuid.uuid4()),
        name="JPMorgan Chase Operating Account",
        source_type="BANK",
        file_format="CSV",
        account_identifier="CHASE-OP-4921",
        currency="USD",
    )
    src_gateway = DataSource(
        id=str(uuid.uuid4()),
        name="Stripe US Gateway",
        source_type="PAYMENT_GATEWAY",
        file_format="JSON",
        account_identifier="acct_1M94xStripe",
        currency="USD",
    )
    src_erp = DataSource(
        id=str(uuid.uuid4()),
        name="NetSuite ERP General Ledger",
        source_type="ACCOUNTING",
        file_format="CSV",
        account_identifier="NS-GL-2026",
        currency="USD",
    )
    src_invoice = DataSource(
        id=str(uuid.uuid4()),
        name="QuickBooks Billing Feed",
        source_type="INVOICE",
        file_format="CSV",
        account_identifier="QB-INV-FEED",
        currency="USD",
    )
    src_crypto = DataSource(
        id=str(uuid.uuid4()),
        name="Ethereum & Polygon Corporate Treasury",
        source_type="CRYPTO",
        file_format="JSON",
        account_identifier="0x71C8364437a9C47F65630C45159392C",
        currency="USD",
    )
    db.add_all([src_bank, src_gateway, src_erp, src_invoice, src_crypto])
    db.commit()

    # 2. Create Entities
    entity_acme = Entity(
        id=str(uuid.uuid4()),
        name="Acme Corp",
        legal_name="Acme Corporation LLC",
        entity_type="CUSTOMER",
        tax_id="12-3456789",
        email="billing@acme.com",
        phone="+1-555-0192",
        wallet_address="0x71C8364437a9C47F65630C45159392C1a5641",
    )
    entity_starlight = Entity(
        id=str(uuid.uuid4()),
        name="Starlight Technologies",
        legal_name="Starlight Tech Systems Inc",
        entity_type="CUSTOMER",
        tax_id="98-7654321",
        email="finance@starlight.tech",
        phone="+1-555-0481",
        wallet_address="0x28C6c06298d514Db089934071355E5743bf21d60",
    )
    entity_cloudscale = Entity(
        id=str(uuid.uuid4()),
        name="CloudScale Hosting",
        legal_name="CloudScale Infrastructure Ltd",
        entity_type="VENDOR",
        tax_id="45-6789012",
        email="invoicing@cloudscale.net",
    )
    entity_apex = Entity(
        id=str(uuid.uuid4()),
        name="Apex Capital",
        legal_name="Apex Capital Management LP",
        entity_type="PARTNER",
        tax_id="55-1234567",
        email="investor-relations@apexcap.com",
    )
    db.add_all([entity_acme, entity_starlight, entity_cloudscale, entity_apex])
    db.commit()

    today = date(2026, 9, 29)
    now = datetime(2026, 9, 29, 14, 30, 0, tzinfo=timezone.utc)

    # 3. Scenario 1: EXACT MATCH (Bank <-> Gateway <-> Invoice)
    # Acme Corp pays $50,000 for INV-1001. All fields align 100%.
    inv_1001 = Invoice(
        id=str(uuid.uuid4()),
        invoice_number="INV-2026-1001",
        entity_id=entity_acme.id,
        issuer_name="FinRecon Global",
        recipient_name="Acme Corp",
        recipient_email="billing@acme.com",
        total_amount=Decimal("50000.00"),
        paid_amount=Decimal("50000.00"),
        currency="USD",
        issue_date=today - timedelta(days=5),
        status="PAID",
        reference_order_id="ORD-1001",
    )
    db.add(inv_1001)

    txn_bank_exact = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-0101",
        entity_id=entity_acme.id,
        counterparty_raw_name="ACME CORP WIRE",
        counterparty_normalized_name="acme corp",
        amount=Decimal("50000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("50000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        transaction_timestamp=now,
        reference_number="REF-1001-EXACT",
        invoice_reference="INV-2026-1001",
        description="Wire Credit Acme Corp INV-2026-1001",
        status="SETTLED",
    )
    txn_gateway_exact = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_gateway.id,
        source_type="PAYMENT_GATEWAY",
        external_transaction_id="ch_3M9qExact1001",
        entity_id=entity_acme.id,
        counterparty_raw_name="Acme Corporation LLC",
        counterparty_normalized_name="acme corp",
        amount=Decimal("50000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("50000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        transaction_timestamp=now,
        reference_number="REF-1001-EXACT",
        invoice_reference="INV-2026-1001",
        description="Stripe Checkout Payment for INV-2026-1001",
        status="SETTLED",
    )
    db.add_all([txn_bank_exact, txn_gateway_exact])
    db.commit()

    case_exact = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0001",
        title="Exact Match: Acme Corp INV-2026-1001",
        status="RECONCILED",
        priority="LOW",
        primary_source_type="BANK",
        total_variance_amount=Decimal("0.00"),
        total_date_variance_days=0,
    )
    db.add(case_exact)
    db.commit()

    match_exact = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_exact.id,
        source_transaction_id=txn_bank_exact.id,
        matched_transaction_id=txn_gateway_exact.id,
        invoice_id=inv_1001.id,
        match_type="TXN_TO_TXN",
        match_status="EXACT_MATCH",
        confidence_score=100.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_1_EXACT",
        evidence_json=json.dumps({
            "amount_diff": 0.0,
            "date_diff_days": 0,
            "reference_match": True,
            "entity_score": 100.0,
            "details": ["Exact reference match: REF-1001-EXACT", "Amounts match exactly: $50,000.00", "Same calendar date"]
        }),
    )
    db.add(match_exact)

    # 4. Scenario 2: PARTIAL MATCH (Amount Discrepancy - Gateway Processing Fee)
    # Starlight Tech pays $20,000 gross. Stripe fee is $580. Bank deposits net $19,420.
    txn_gateway_fee = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_gateway.id,
        source_type="PAYMENT_GATEWAY",
        external_transaction_id="ch_fee_starlight_2002",
        entity_id=entity_starlight.id,
        counterparty_raw_name="Starlight Tech Systems",
        counterparty_normalized_name="starlight tech",
        amount=Decimal("20000.00"),
        fee_amount=Decimal("580.00"),
        net_amount=Decimal("19420.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        reference_number="ORD-2002-FEE",
        description="Gross charge $20,000, 2.9% fee deduction",
        status="SETTLED",
    )
    txn_bank_fee = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-0202",
        entity_id=entity_starlight.id,
        counterparty_raw_name="STRIPE PAYOUT STARLIGHT",
        counterparty_normalized_name="starlight tech",
        amount=Decimal("19420.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("19420.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        reference_number="ORD-2002-FEE",
        description="Stripe Payout Net Deposit for ORD-2002-FEE",
        status="SETTLED",
    )
    db.add_all([txn_gateway_fee, txn_bank_fee])
    db.commit()

    case_fee = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0002",
        title="Amount Discrepancy: Starlight Tech Gateway Fee Variance",
        status="UNDER_REVIEW",
        priority="HIGH",
        primary_source_type="PAYMENT_GATEWAY",
        total_variance_amount=Decimal("580.00"),
        total_date_variance_days=0,
    )
    db.add(case_fee)
    db.commit()

    match_fee = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_fee.id,
        source_transaction_id=txn_gateway_fee.id,
        matched_transaction_id=txn_bank_fee.id,
        match_type="TXN_TO_TXN",
        match_status="PARTIAL_MATCH",
        confidence_score=94.5,
        confidence_level="HIGH",
        algorithm_pass="PASS_2_ID_CORRELATION",
        evidence_json=json.dumps({
            "amount_diff": 580.0,
            "amount_diff_pct": 2.9,
            "reference_match": True,
            "entity_score": 96.0,
            "details": ["Reference ORD-2002-FEE aligns", "Amount variance of $580.00 exactly matches Stripe 2.9% fee schedule"]
        }),
    )
    db.add(match_fee)
    db.commit()

    disc_amount = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_fee.id,
        match_id=match_fee.id,
        discrepancy_type="AMOUNT",
        field_name="amount",
        source_value="20000.00",
        matched_value="19420.00",
        difference_numeric=Decimal("580.00"),
        difference_percentage=2.9,
        root_cause_category="PROCESSING_FEE",
        severity="MEDIUM",
    )
    db.add(disc_amount)

    # 5. Scenario 3: PARTIAL MATCH (Date Discrepancy - T+3 Bank Settlement Lag)
    # Payment authorized on Gateway on Friday Sep 25, credited in Bank on Wednesday Sep 30 ($15,000).
    txn_gateway_lag = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_gateway.id,
        source_type="PAYMENT_GATEWAY",
        external_transaction_id="ch_lag_3003",
        entity_id=entity_cloudscale.id,
        counterparty_raw_name="CloudScale Infrastructure",
        counterparty_normalized_name="cloudscale hosting",
        amount=Decimal("15000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("15000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today - timedelta(days=4),  # Sep 25
        reference_number="REF-LAG-3003",
        description="Vendor settlement captured Friday",
        status="SETTLED",
    )
    txn_bank_lag = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-0303",
        entity_id=entity_cloudscale.id,
        counterparty_raw_name="CloudScale Hosting Ltd",
        counterparty_normalized_name="cloudscale hosting",
        amount=Decimal("15000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("15000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today + timedelta(days=1),  # Sep 30 (5-day lag across weekend)
        reference_number="REF-LAG-3003",
        description="Direct ACH credit from CloudScale",
        status="SETTLED",
    )
    db.add_all([txn_gateway_lag, txn_bank_lag])
    db.commit()

    case_lag = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0003",
        title="Date Discrepancy: CloudScale T+3 Weekend Lag",
        status="OPEN",
        priority="MEDIUM",
        primary_source_type="BANK",
        total_variance_amount=Decimal("0.00"),
        total_date_variance_days=5,
    )
    db.add(case_lag)
    db.commit()

    match_lag = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_lag.id,
        source_transaction_id=txn_bank_lag.id,
        matched_transaction_id=txn_gateway_lag.id,
        match_type="TXN_TO_TXN",
        match_status="PARTIAL_MATCH",
        confidence_score=88.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_3_RAPIDFUZZ",
        evidence_json=json.dumps({
            "amount_diff": 0.0,
            "date_diff_days": 5,
            "reference_match": True,
            "details": ["Amount matches: $15,000.00", "Settlement date shifted by 5 days (T+3 + weekend)"]
        }),
    )
    db.add(match_lag)
    db.commit()

    disc_date = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_lag.id,
        match_id=match_lag.id,
        discrepancy_type="DATE",
        field_name="transaction_date",
        source_value=str(today + timedelta(days=1)),
        matched_value=str(today - timedelta(days=4)),
        difference_numeric=Decimal("5.00"),
        difference_percentage=0.0,
        root_cause_category="T_PLUS_LAG",
        severity="LOW",
    )
    db.add(disc_date)

    # 6. Scenario 4: DUPLICATE RECORD (Replayed Webhook / Accidental Double Entry)
    # The bank statement records the same charge $8,450 twice with identical check number.
    txn_dup_original = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-DUP-A",
        entity_id=entity_acme.id,
        counterparty_raw_name="Acme Corp Wire Check",
        counterparty_normalized_name="acme corp",
        amount=Decimal("8450.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("8450.00"),
        currency="USD",
        direction="DEBIT",
        transaction_date=today,
        reference_number="CHK-994821",
        description="Check payment #994821 to vendor",
        status="SETTLED",
    )
    txn_dup_replayed = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-DUP-B",
        entity_id=entity_acme.id,
        counterparty_raw_name="Acme Corp Wire Check",
        counterparty_normalized_name="acme corp",
        amount=Decimal("8450.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("8450.00"),
        currency="USD",
        direction="DEBIT",
        transaction_date=today,
        reference_number="CHK-994821",
        description="Duplicate replayed entry for Check #994821",
        status="SETTLED",
    )
    db.add_all([txn_dup_original, txn_dup_replayed])
    db.commit()

    case_dup = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0004",
        title="Duplicate Transaction Flagged: Check #994821",
        status="OPEN",
        priority="CRITICAL",
        primary_source_type="BANK",
        total_variance_amount=Decimal("8450.00"),
        total_date_variance_days=0,
    )
    db.add(case_dup)
    db.commit()

    match_dup = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_dup.id,
        source_transaction_id=txn_dup_original.id,
        matched_transaction_id=txn_dup_replayed.id,
        match_type="DUPLICATE_PAIR",
        match_status="DUPLICATE",
        confidence_score=99.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_5_ANOMALY",
        evidence_json=json.dumps({
            "duplicate_signal": "Identical amount $8,450, same source Bank, same date, identical check ref CHK-994821",
            "details": ["Probable accidental double ledger import or duplicate clearing batch"]
        }),
    )
    db.add(match_dup)
    db.commit()

    disc_dup = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_dup.id,
        match_id=match_dup.id,
        discrepancy_type="DUPLICATE_ENTRY",
        field_name="external_transaction_id",
        source_value=txn_dup_original.external_transaction_id,
        matched_value=txn_dup_replayed.external_transaction_id,
        difference_numeric=Decimal("8450.00"),
        root_cause_category="DUPLICATE_WEBHOOK",
        severity="CRITICAL",
    )
    db.add(disc_dup)

    # 7. Scenario 5: MISSING RECORD (Orphaned Bank Fee)
    # A $120.00 bank maintenance/wire fee charged on Chase but never recorded in NetSuite ERP.
    txn_orphan_bank = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-FEE-5005",
        counterparty_raw_name="JPMORGAN WIRE SERVICE FEE",
        counterparty_normalized_name="jpmorgan chase",
        amount=Decimal("120.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("120.00"),
        currency="USD",
        direction="DEBIT",
        transaction_date=today,
        reference_number="WIRE-FEE-5005",
        description="Monthly foreign outgoing wire maintenance fee",
        status="SETTLED",
    )
    db.add(txn_orphan_bank)
    db.commit()

    case_orphan = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0005",
        title="Missing Record in Accounting: Unrecorded Wire Fee $120.00",
        status="OPEN",
        priority="MEDIUM",
        primary_source_type="BANK",
        total_variance_amount=Decimal("120.00"),
        total_date_variance_days=0,
    )
    db.add(case_orphan)
    db.commit()

    match_orphan = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_orphan.id,
        source_transaction_id=txn_orphan_bank.id,
        match_type="TXN_TO_TXN",
        match_status="MISSING_RECORD",
        confidence_score=0.0,
        confidence_level="LOW",
        algorithm_pass="PASS_5_ANOMALY",
        evidence_json=json.dumps({
            "details": ["Transaction present in Bank Statement but 0 matching entries found in NetSuite ERP or Invoices"]
        }),
    )
    db.add(match_orphan)
    db.commit()

    disc_missing = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_orphan.id,
        match_id=match_orphan.id,
        discrepancy_type="MISSING_ENTRY",
        field_name="accounting_entry",
        source_value="$120.00 (Bank)",
        matched_value="NONE (Accounting)",
        difference_numeric=Decimal("120.00"),
        root_cause_category="UNRECORDED_EXPENSE",
        severity="MEDIUM",
    )
    db.add(disc_missing)

    # 8. Scenario 6: CONFLICTING RECORDS (Same Reference, Contradictory Entities)
    # Order ORD-6006 has $30,000 paid. ERP ledger says "Acme Corp", Bank statement says wire went to "Apex Capital".
    txn_erp_conflict = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_erp.id,
        source_type="ACCOUNTING",
        external_transaction_id="NS-JE-6006",
        entity_id=entity_acme.id,
        counterparty_raw_name="Acme Corp",
        counterparty_normalized_name="acme corp",
        amount=Decimal("30000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("30000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        reference_number="ORD-CONFLICT-6006",
        description="Accounting ledger records Acme Corp order payment",
        status="SETTLED",
    )
    txn_bank_conflict = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_bank.id,
        source_type="BANK",
        external_transaction_id="BANK-TXN-6006",
        entity_id=entity_apex.id,
        counterparty_raw_name="Apex Capital Management",
        counterparty_normalized_name="apex capital",
        amount=Decimal("30000.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("30000.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        reference_number="ORD-CONFLICT-6006",
        description="Bank incoming transfer marked with ORD-CONFLICT-6006 from Apex Capital",
        status="SETTLED",
    )
    db.add_all([txn_erp_conflict, txn_bank_conflict])
    db.commit()

    case_conflict = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0006",
        title="Conflicting Records: ORD-CONFLICT-6006 Entity Mismatch",
        status="ESCALATED",
        priority="CRITICAL",
        primary_source_type="ACCOUNTING",
        total_variance_amount=Decimal("0.00"),
        total_date_variance_days=0,
    )
    db.add(case_conflict)
    db.commit()

    match_conflict = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_conflict.id,
        source_transaction_id=txn_erp_conflict.id,
        matched_transaction_id=txn_bank_conflict.id,
        match_type="TXN_TO_TXN",
        match_status="CONFLICTING_RECORD",
        confidence_score=62.0,
        confidence_level="MEDIUM",
        algorithm_pass="PASS_5_ANOMALY",
        evidence_json=json.dumps({
            "reference_match": True,
            "entity_score": 12.0,
            "details": [
                "Reference ORD-CONFLICT-6006 is identical in both systems",
                "Amounts align: $30,000.00",
                "CRITICAL CONFLICT: ERP entity 'Acme Corp' conflicts with Bank entity 'Apex Capital'"
            ]
        }),
    )
    db.add(match_conflict)
    db.commit()

    disc_conflict = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_conflict.id,
        match_id=match_conflict.id,
        discrepancy_type="ENTITY",
        field_name="counterparty_name",
        source_value="Acme Corp",
        matched_value="Apex Capital",
        root_cause_category="DATA_ENTRY_ERROR",
        severity="CRITICAL",
    )
    db.add(disc_conflict)

    # 9. Scenario 7: CRYPTO-TO-INVOICE MATCH (Ethereum USDT <-> Invoice)
    # Starlight Tech settles $10,000 invoice via Ethereum USDT transfer.
    inv_crypto = Invoice(
        id=str(uuid.uuid4()),
        invoice_number="INV-2026-7007",
        entity_id=entity_starlight.id,
        issuer_name="FinRecon Global",
        recipient_name="Starlight Tech",
        recipient_email="finance@starlight.tech",
        total_amount=Decimal("10000.00"),
        paid_amount=Decimal("10000.00"),
        currency="USD",
        issue_date=today - timedelta(days=2),
        status="PAID",
        crypto_wallet_dest="0x71C8364437a9C47F65630C45159392C1a5641",
    )
    db.add(inv_crypto)

    crypto_tx_usdt = CryptoTransaction(
        id=str(uuid.uuid4()),
        source_id=src_crypto.id,
        transaction_hash="0x4a9f39d8e5781a98230bcf92158f902517865c3289196b05df82c974836109fe",
        blockchain_network="ETHEREUM",
        wallet_from="0x28C6c06298d514Db089934071355E5743bf21d60",
        wallet_to="0x71C8364437a9C47F65630C45159392C1a5641",
        asset="USDT",
        token_amount=Decimal("10000.00000000"),
        fiat_value=Decimal("10000.00"),
        fiat_currency="USD",
        transaction_timestamp=now,
        block_number=20891234,
        gas_fee=Decimal("0.00421000"),
        gas_fee_fiat=Decimal("11.50"),
        confirmation_status="CONFIRMED",
        associated_invoice_id="INV-2026-7007",
        associated_reference="STARLIGHT-USDT-SETTLE",
    )
    db.add(crypto_tx_usdt)
    db.commit()

    case_crypto_inv = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0007",
        title="Crypto-to-Invoice Match: Starlight Tech 10,000 USDT",
        status="RECONCILED",
        priority="LOW",
        primary_source_type="CRYPTO",
        total_variance_amount=Decimal("0.00"),
        total_date_variance_days=0,
    )
    db.add(case_crypto_inv)
    db.commit()

    match_crypto_inv = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_crypto_inv.id,
        crypto_transaction_id=crypto_tx_usdt.id,
        invoice_id=inv_crypto.id,
        match_type="CRYPTO_TO_INVOICE",
        match_status="EXACT_MATCH",
        confidence_score=98.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_4_CRYPTO_MATCH",
        evidence_json=json.dumps({
            "hash": crypto_tx_usdt.transaction_hash,
            "fiat_diff": 0.0,
            "wallet_match": True,
            "invoice_match": True,
            "details": [
                "10,000 USDT matches $10,000.00 invoice balance",
                "Destination wallet verified: 0x71C8...1a5641",
                "Invoice ID INV-2026-7007 found in transaction metadata payload"
            ]
        }),
    )
    db.add(match_crypto_inv)

    # 10. Scenario 8: CRYPTO-TO-ACCOUNTING MATCH (Polygon USDC <-> ERP Journal Entry)
    # CloudScale Hosting pays $2,500 USDC for infrastructure maintenance.
    txn_erp_crypto = Transaction(
        id=str(uuid.uuid4()),
        source_id=src_erp.id,
        source_type="ACCOUNTING",
        external_transaction_id="NS-JE-8008",
        entity_id=entity_cloudscale.id,
        counterparty_raw_name="CloudScale Infrastructure Ltd",
        counterparty_normalized_name="cloudscale hosting",
        amount=Decimal("2500.00"),
        fee_amount=Decimal("0.00"),
        net_amount=Decimal("2500.00"),
        currency="USD",
        direction="CREDIT",
        transaction_date=today,
        reference_number="POLY-USDC-8008",
        description="USDC Treasury settlement for Cloud Hosting service",
        status="SETTLED",
    )
    db.add(txn_erp_crypto)

    crypto_tx_poly = CryptoTransaction(
        id=str(uuid.uuid4()),
        source_id=src_crypto.id,
        transaction_hash="0x9e8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a",
        blockchain_network="POLYGON",
        wallet_from="0x4567890abcdef1234567890abcdef1234567890a",
        wallet_to="0x71C8364437a9C47F65630C45159392C1a5641",
        asset="USDC",
        token_amount=Decimal("2500.00000000"),
        fiat_value=Decimal("2500.00"),
        fiat_currency="USD",
        transaction_timestamp=now,
        block_number=62194821,
        gas_fee=Decimal("0.02500000"),
        gas_fee_fiat=Decimal("0.02"),
        confirmation_status="CONFIRMED",
        associated_reference="POLY-USDC-8008",
    )
    db.add(crypto_tx_poly)
    db.commit()

    case_crypto_erp = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0008",
        title="Crypto-to-Accounting Match: CloudScale 2,500 USDC on Polygon",
        status="RECONCILED",
        priority="LOW",
        primary_source_type="CRYPTO",
        total_variance_amount=Decimal("0.00"),
        total_date_variance_days=0,
    )
    db.add(case_crypto_erp)
    db.commit()

    match_crypto_erp = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_crypto_erp.id,
        source_transaction_id=txn_erp_crypto.id,
        crypto_transaction_id=crypto_tx_poly.id,
        match_type="CRYPTO_TO_ERP",
        match_status="EXACT_MATCH",
        confidence_score=97.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_4_CRYPTO_MATCH",
        evidence_json=json.dumps({
            "hash": crypto_tx_poly.transaction_hash,
            "fiat_diff": 0.0,
            "network": "POLYGON",
            "details": ["2,500 USDC on Polygon matches NetSuite Journal Entry #NS-JE-8008", "Reference POLY-USDC-8008 verified"]
        }),
    )
    db.add(match_crypto_erp)

    # 11. Scenario 9: CRYPTO AMOUNT DISCREPANCY (ETH Fiat Valuation Slippage)
    # Invoice for $3,500 paid in ETH (1.12 ETH). At time of settlement ETH dipped, fiat value was $3,485.50 ($14.50 variance).
    inv_eth = Invoice(
        id=str(uuid.uuid4()),
        invoice_number="INV-2026-9009",
        entity_id=entity_acme.id,
        issuer_name="FinRecon Global",
        recipient_name="Acme Corp",
        total_amount=Decimal("3500.00"),
        paid_amount=Decimal("3485.50"),
        currency="USD",
        issue_date=today,
        status="PARTIALLY_PAID",
    )
    crypto_tx_eth = CryptoTransaction(
        id=str(uuid.uuid4()),
        source_id=src_crypto.id,
        transaction_hash="0x7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e",
        blockchain_network="ETHEREUM",
        wallet_from="0x71C8364437a9C47F65630C45159392C1a5641",
        wallet_to="0x9999999999999999999999999999999999999999",
        asset="ETH",
        token_amount=Decimal("1.12000000"),
        fiat_value=Decimal("3485.50"),
        fiat_currency="USD",
        transaction_timestamp=now,
        block_number=20891450,
        gas_fee=Decimal("0.00350000"),
        gas_fee_fiat=Decimal("9.80"),
        confirmation_status="CONFIRMED",
        associated_invoice_id="INV-2026-9009",
    )
    db.add_all([inv_eth, crypto_tx_eth])
    db.commit()

    case_eth_slippage = ReconciliationCase(
        id=str(uuid.uuid4()),
        case_number="CASE-2026-0009",
        title="Crypto Valuation Discrepancy: Acme Corp ETH Slippage ($14.50)",
        status="UNDER_REVIEW",
        priority="MEDIUM",
        primary_source_type="CRYPTO",
        total_variance_amount=Decimal("14.50"),
        total_date_variance_days=0,
    )
    db.add(case_eth_slippage)
    db.commit()

    match_eth_slippage = ReconciliationMatch(
        id=str(uuid.uuid4()),
        case_id=case_eth_slippage.id,
        crypto_transaction_id=crypto_tx_eth.id,
        invoice_id=inv_eth.id,
        match_type="CRYPTO_TO_INVOICE",
        match_status="PARTIAL_MATCH",
        confidence_score=92.0,
        confidence_level="HIGH",
        algorithm_pass="PASS_4_CRYPTO_MATCH",
        evidence_json=json.dumps({
            "invoice_amount": 3500.0,
            "crypto_fiat_value": 3485.5,
            "difference": 14.5,
            "details": ["Invoice INV-2026-9009 for $3,500 settled with 1.12 ETH", "ETH/USD rate change created $14.50 slippage variance"]
        }),
    )
    db.add(match_eth_slippage)
    db.commit()

    disc_eth = DiscrepancyRecord(
        id=str(uuid.uuid4()),
        case_id=case_eth_slippage.id,
        match_id=match_eth_slippage.id,
        discrepancy_type="AMOUNT",
        field_name="fiat_value",
        source_value="3500.00",
        matched_value="3485.50",
        difference_numeric=Decimal("14.50"),
        difference_percentage=0.41,
        root_cause_category="FX_RATE_SHIFT",
        severity="LOW",
    )
    db.add(disc_eth)

    # 12. Add Manual Reviews and Audit Logs
    review_fee = ManualReview(
        id=str(uuid.uuid4()),
        case_id=case_fee.id,
        match_id=match_fee.id,
        reviewer_name="Praveen (Lead Financial Analyst)",
        action="CONFIRM_MATCH",
        previous_status="OPEN",
        new_status="UNDER_REVIEW",
        notes="Verified variance corresponds to Stripe standard 2.9% transaction fee. Schedule fee adjustment entry in ERP.",
    )
    db.add(review_fee)

    audit_1 = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="CASE",
        entity_id=case_exact.id,
        case_id=case_exact.id,
        actor_type="SYSTEM_ENGINE",
        actor_id="ENGINE_PASS_1",
        action="AUTO_MATCH_CREATED",
        details="Automated 100% exact match resolved across Chase Bank, Stripe, and Invoice INV-2026-1001",
    )
    audit_2 = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="CASE",
        entity_id=case_fee.id,
        case_id=case_fee.id,
        actor_type="MANUAL_REVIEWER",
        actor_id="user_praveen",
        action="MANUAL_OVERRIDE",
        old_state=json.dumps({"status": "OPEN"}),
        new_state=json.dumps({"status": "UNDER_REVIEW", "notes": "Fee schedule verified"}),
        details="Reviewer confirmed Stripe 2.9% fee variance of $580.00",
    )
    audit_3 = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="CASE",
        entity_id=case_dup.id,
        case_id=case_dup.id,
        actor_type="SYSTEM_ENGINE",
        actor_id="ENGINE_PASS_5",
        action="DISCREPANCY_FLAGGED",
        details="CRITICAL duplicate charge detected on Chase statement: Check #994821 ($8,450.00)",
    )
    db.add_all([audit_1, audit_2, audit_3])
    db.commit()

    summary = {
        "data_sources": db.query(DataSource).count(),
        "entities": db.query(Entity).count(),
        "transactions": db.query(Transaction).count(),
        "invoices": db.query(Invoice).count(),
        "crypto_transactions": db.query(CryptoTransaction).count(),
        "reconciliation_cases": db.query(ReconciliationCase).count(),
        "reconciliation_matches": db.query(ReconciliationMatch).count(),
        "discrepancy_records": db.query(DiscrepancyRecord).count(),
        "manual_reviews": db.query(ManualReview).count(),
        "audit_logs": db.query(AuditLog).count(),
    }
    logger.info(f"Database successfully seeded! Summary: {summary}")
    return summary


if __name__ == "__main__":
    db = SessionLocal()
    try:
        summary = seed_database(db)
        print("SEEDING SUCCESSFUL:")
        print(json.dumps(summary, indent=2))
    finally:
        db.close()
