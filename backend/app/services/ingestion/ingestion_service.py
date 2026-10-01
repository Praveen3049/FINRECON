from datetime import datetime, timezone
from decimal import Decimal
import json
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import DataSource, Entity, Transaction, Invoice, CryptoTransaction, AuditLog
from app.services.audit.service import AuditService
from app.services.ingestion.file_parser import FileParser
from app.services.ingestion.column_detector import ColumnDetector
from app.services.ingestion.validator import RowValidator
from app.core.logging import logger


class IngestionService:
    @staticmethod
    def process_file_upload(
        db: Session,
        content: bytes,
        filename: str,
        source_type: str,
        source_name: Optional[str] = None,
        account_id: Optional[str] = None,
        account_identifier: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Processes multi-source file uploads (CSV, JSON, XLSX), detects schema,
        normalizes data, stores records, and returns an ingestion summary.
        """
        source_type = source_type.upper()
        if source_type not in ["BANK", "PAYMENT_GATEWAY", "ACCOUNTING", "INVOICE", "CRYPTO"]:
            raise ValueError(f"Unsupported source type: {source_type}")

        # 1. Parse file content
        raw_rows, detected_format = FileParser.parse_file(content, filename)
        total_records = len(raw_rows)
        if total_records == 0:
            return {
                "file_name": filename,
                "source_type": source_type,
                "total_records": 0,
                "processed_records": 0,
                "failed_records": 0,
                "warnings": ["The uploaded file contained 0 rows or valid headers."],
                "detected_columns": {},
                "preview": []
            }

        # 2. Detect column mapping
        first_row_headers = list(raw_rows[0].keys())
        column_mapping = ColumnDetector.detect_mapping(first_row_headers)
        
        warnings = []
        if len(column_mapping) < 2:
            warnings.append("Low column confidence: headers did not match standard financial templates.")

        # 3. Create or resolve DataSource
        data_source = None
        if account_id:
            data_source = db.query(DataSource).filter_by(id=account_id).first()

        if not data_source and source_name:
            data_source = db.query(DataSource).filter_by(name=source_name).first()

        if not data_source:
            resolved_source_name = source_name or f"{source_type.title()} Feed ({filename})"
            data_source = DataSource(
                id=account_id or str(uuid.uuid4()),
                name=resolved_source_name,
                source_type=source_type,
                file_format=detected_format,
                account_identifier=account_identifier or f"ACC-{datetime.now().strftime('%Y%m%d%H%M')}",
                currency="INR" if "INR" in filename.upper() or "ACZEN" in filename.upper() else "USD",
                owner_id=owner_id,
            )
            db.add(data_source)
            db.commit()
        elif owner_id and not data_source.owner_id:
            data_source.owner_id = owner_id
            db.commit()

        # 4. Ingest and normalize records
        processed_count = 0
        failed_count = 0
        canonical_preview = []

        for idx, row in enumerate(raw_rows):
            try:
                # Apply column mapping
                mapped_data: Dict[str, Any] = {}
                for raw_col, val in row.items():
                    canonical_key = column_mapping.get(raw_col, raw_col.lower())
                    mapped_data[canonical_key] = val

                if source_type == "CRYPTO":
                    # Process Crypto Transaction
                    is_valid, row_errors = RowValidator.validate_crypto_row(mapped_data)
                    if not is_valid:
                        warnings.extend([f"Row {idx+1}: {err}" for err in row_errors])
                        failed_count += 1
                        continue

                    tx_hash = str(mapped_data.get("transaction_hash") or mapped_data.get("tx_hash") or f"0x{uuid.uuid4().hex}")
                    # Check duplicate hash
                    existing = db.query(CryptoTransaction).filter_by(transaction_hash=tx_hash).first()
                    if existing:
                        warnings.append(f"Row {idx+1}: Duplicate hash {tx_hash[:12]} skipped.")
                        failed_count += 1
                        continue

                    raw_token_amount = mapped_data.get("token_amount") or mapped_data.get("amount") or 0.0
                    token_num, _ = RowValidator.parse_amount(raw_token_amount)
                    raw_fiat = mapped_data.get("fiat_value") or raw_token_amount
                    fiat_num, _ = RowValidator.parse_amount(raw_fiat)
                    tx_date, tx_datetime = RowValidator.parse_date(mapped_data.get("transaction_timestamp") or mapped_data.get("timestamp"))

                    crypto_tx = CryptoTransaction(
                        id=str(uuid.uuid4()),
                        source_id=data_source.id,
                        transaction_hash=tx_hash,
                        blockchain_network=str(mapped_data.get("blockchain_network") or mapped_data.get("network") or "ETHEREUM").upper(),
                        wallet_from=str(mapped_data.get("wallet_from") or mapped_data.get("from") or "0x0000000000000000000000000000000000000000"),
                        wallet_to=str(mapped_data.get("wallet_to") or mapped_data.get("to") or "0x0000000000000000000000000000000000000000"),
                        asset=str(mapped_data.get("asset") or mapped_data.get("token") or "USDT").upper(),
                        token_amount=token_num,
                        fiat_value=fiat_num,
                        fiat_currency=str(mapped_data.get("fiat_currency") or "USD").upper(),
                        transaction_timestamp=tx_datetime or datetime.now(timezone.utc),
                        block_number=int(mapped_data.get("block_number")) if mapped_data.get("block_number") else None,
                        gas_fee=Decimal(str(mapped_data.get("gas_fee"))) if mapped_data.get("gas_fee") else None,
                        confirmation_status=str(mapped_data.get("confirmation_status") or "CONFIRMED").upper(),
                        associated_invoice_id=mapped_data.get("associated_invoice_id") or mapped_data.get("invoice_reference"),
                        associated_reference=mapped_data.get("associated_reference") or mapped_data.get("reference_number"),
                    )
                    db.add(crypto_tx)
                    processed_count += 1
                    if len(canonical_preview) < 5:
                        canonical_preview.append({
                            "type": "CRYPTO",
                            "hash": tx_hash[:16] + "...",
                            "asset": crypto_tx.asset,
                            "amount": float(token_num),
                            "fiat_value": float(fiat_num),
                            "network": crypto_tx.blockchain_network,
                        })

                elif source_type == "INVOICE":
                    # Process Invoice
                    inv_num = str(mapped_data.get("invoice_number") or mapped_data.get("invoice_id") or f"INV-{uuid.uuid4().hex[:8].upper()}")
                    raw_amount = mapped_data.get("total_amount") or mapped_data.get("amount") or 0.0
                    tot_num, _ = RowValidator.parse_amount(raw_amount)
                    issue_d, _ = RowValidator.parse_date(mapped_data.get("issue_date") or mapped_data.get("transaction_date"))
                    due_d, _ = RowValidator.parse_date(mapped_data.get("due_date")) if mapped_data.get("due_date") else (None, None)

                    invoice = Invoice(
                        id=str(uuid.uuid4()),
                        invoice_number=inv_num,
                        issuer_name=str(mapped_data.get("issuer_name") or "FinRecon Global"),
                        recipient_name=str(mapped_data.get("counterparty") or mapped_data.get("customer_name") or "Counterparty"),
                        recipient_email=mapped_data.get("customer_email"),
                        total_amount=tot_num,
                        paid_amount=Decimal("0.00"),
                        currency=str(mapped_data.get("currency") or "USD").upper(),
                        issue_date=issue_d,
                        due_date=due_d,
                        status=str(mapped_data.get("status") or "ISSUED").upper(),
                        reference_order_id=mapped_data.get("reference_number") or mapped_data.get("po_number"),
                        crypto_wallet_dest=mapped_data.get("crypto_destination_wallet") or mapped_data.get("wallet_to"),
                    )
                    db.add(invoice)
                    processed_count += 1
                    if len(canonical_preview) < 5:
                        canonical_preview.append({
                            "type": "INVOICE",
                            "invoice_number": inv_num,
                            "recipient": invoice.recipient_name,
                            "amount": float(tot_num),
                            "status": invoice.status,
                        })

                else:
                    # Process Standard Transaction (BANK, PAYMENT_GATEWAY, ACCOUNTING)
                    external_id = str(
                        mapped_data.get("transaction_id") or 
                        mapped_data.get("charge_id") or 
                        mapped_data.get("journal_id") or 
                        f"TXN-{uuid.uuid4().hex[:8].upper()}"
                    )
                    raw_amount = mapped_data.get("amount") or mapped_data.get("debit") or mapped_data.get("credit") or 0.0
                    amount_num, default_dir = RowValidator.parse_amount(raw_amount)
                    
                    # Direction determination
                    explicit_dir = str(mapped_data.get("direction") or "").upper()
                    if explicit_dir in ["CREDIT", "CR", "INFLOW", "DEPOSIT"]:
                        direction = "CREDIT"
                    elif explicit_dir in ["DEBIT", "DR", "OUTFLOW", "WITHDRAWAL", "PAYMENT"]:
                        direction = "DEBIT"
                    else:
                        direction = default_dir

                    # Fee & Net amounts
                    fee_num, _ = RowValidator.parse_amount(mapped_data.get("fee_amount") or mapped_data.get("fee") or 0.0)
                    net_num, _ = RowValidator.parse_amount(mapped_data.get("net_amount") or mapped_data.get("net")) if (mapped_data.get("net_amount") or mapped_data.get("net")) else (amount_num - fee_num, "CREDIT")

                    tx_date, tx_datetime = RowValidator.parse_date(
                        mapped_data.get("transaction_date") or 
                        mapped_data.get("transaction_timestamp") or 
                        mapped_data.get("created")
                    )

                    counterparty_raw = mapped_data.get("counterparty") or mapped_data.get("customer_name") or mapped_data.get("entity_name")
                    counterparty_norm = counterparty_raw.strip().lower() if counterparty_raw else None

                    txn = Transaction(
                        id=str(uuid.uuid4()),
                        source_id=data_source.id,
                        source_type=source_type,
                        external_transaction_id=external_id,
                        counterparty_raw_name=counterparty_raw,
                        counterparty_normalized_name=counterparty_norm,
                        amount=amount_num,
                        fee_amount=fee_num,
                        net_amount=net_num,
                        currency=str(mapped_data.get("currency") or "USD").upper(),
                        direction=direction,
                        transaction_date=tx_date,
                        transaction_timestamp=tx_datetime,
                        reference_number=mapped_data.get("reference_number") or mapped_data.get("reference_utr") or mapped_data.get("ref_number"),
                        invoice_reference=mapped_data.get("invoice_reference") or mapped_data.get("invoice_number"),
                        payment_reference=mapped_data.get("payment_reference") or mapped_data.get("charge_id"),
                        description=mapped_data.get("description") or mapped_data.get("memo"),
                        raw_data=json.dumps(row),
                        status=str(mapped_data.get("status") or "SETTLED").upper(),
                    )
                    db.add(txn)
                    processed_count += 1
                    if len(canonical_preview) < 5:
                        canonical_preview.append({
                            "type": source_type,
                            "external_id": external_id,
                            "counterparty": counterparty_raw or "N/A",
                            "amount": float(amount_num),
                            "direction": direction,
                            "date": str(tx_date),
                        })

            except Exception as e:
                logger.error(f"Error processing row {idx+1}: {e}")
                warnings.append(f"Row {idx+1}: Parsing error: {str(e)}")
                failed_count += 1

        db.commit()

        # 5. Log Ingestion Audit Log with cryptographic SHA-256 chained hash
        AuditService.create_log(
            db=db,
            entity_type="DATA_SOURCE",
            entity_id=data_source.id,
            actor_type="SYSTEM_ENGINE",
            actor_id="INGESTION_SERVICE",
            action="FILE_INGESTED",
            details=f"Ingested {processed_count} records from {filename} ({source_type}) with {failed_count} failures.",
            new_state={
                "file_name": filename,
                "source_type": source_type,
                "processed": processed_count,
                "failed": failed_count,
            },
        )
        db.commit()

        return {
            "file_name": filename,
            "source_type": source_type,
            "total_records": total_records,
            "processed_records": processed_count,
            "failed_records": failed_count,
            "warnings": warnings[:10],  # Return up to 10 warnings
            "detected_columns": column_mapping,
            "preview": canonical_preview
        }
