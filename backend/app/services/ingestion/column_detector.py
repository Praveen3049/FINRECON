from typing import Dict, List, Optional, Any


class ColumnDetector:
    # Field alias dictionaries (case-insensitive)
    FIELD_ALIASES = {
        "transaction_id": [
            "transaction_id", "txn_id", "tx_id", "external_id", "id",
            "charge_id", "journal_id", "journal_entry", "reference_id"
        ],
        "transaction_date": [
            "transaction_date", "txn_date", "date", "posting_date",
            "value_date", "created_date", "issue_date"
        ],
        "transaction_timestamp": [
            "transaction_timestamp", "timestamp", "created", "created_at",
            "datetime", "time"
        ],
        "amount": [
            "amount", "gross_amount", "gross", "total", "total_amount",
            "transaction_amount", "credit", "debit"
        ],
        "fee_amount": [
            "fee_amount", "fee", "fees", "processing_fee", "charges"
        ],
        "net_amount": [
            "net_amount", "net", "settled_amount", "payout_amount"
        ],
        "direction": [
            "direction", "type", "txn_type", "dr_cr", "credit_debit"
        ],
        "currency": [
            "currency", "curr", "ccy"
        ],
        "counterparty": [
            "counterparty", "counterparty_name", "entity_name", "customer_name",
            "customer", "recipient_name", "vendor_name", "vendor", "payer", "beneficiary"
        ],
        "reference_number": [
            "reference_number", "reference_utr", "reference", "ref_number",
            "ref_no", "utr", "arn", "check_number", "check_no", "chk_no", "po_number"
        ],
        "invoice_reference": [
            "invoice_reference", "invoice_number", "invoice_id", "inv_number", "inv_no"
        ],
        "payment_reference": [
            "payment_reference", "payment_id", "payout_reference", "order_id"
        ],
        "description": [
            "description", "memo", "narration", "details", "notes", "remark"
        ],
        "status": [
            "status", "state", "payment_status", "confirmation_status"
        ],
        # Crypto-specific
        "transaction_hash": [
            "transaction_hash", "tx_hash", "hash", "txn_hash"
        ],
        "blockchain_network": [
            "blockchain_network", "network", "chain", "blockchain"
        ],
        "wallet_from": [
            "wallet_from", "from_wallet", "from_address", "sender", "from"
        ],
        "wallet_to": [
            "wallet_to", "to_wallet", "to_address", "recipient", "receiver", "to"
        ],
        "asset": [
            "asset", "token", "symbol", "coin", "cryptocurrency"
        ],
        "token_amount": [
            "token_amount", "crypto_amount", "tokens", "amount"
        ],
        "fiat_value": [
            "fiat_value", "usd_value", "fiat_amount", "valuation"
        ],
        "gas_fee": [
            "gas_fee", "gas", "tx_fee", "network_fee"
        ],
        "block_number": [
            "block_number", "block", "block_height"
        ],
    }

    @classmethod
    def detect_mapping(cls, headers: List[str]) -> Dict[str, str]:
        """
        Maps source raw header names to canonical schema fields.
        Returns: { source_header: canonical_field }
        """
        mapping: Dict[str, str] = {}
        assigned_canonical: set = set()

        for header in headers:
            clean_header = header.lower().strip().replace(" ", "_").replace("-", "_").replace(".", "")
            
            # Check exact or prefix/suffix match in alias dictionary
            matched_field: Optional[str] = None
            for canonical_field, aliases in cls.FIELD_ALIASES.items():
                if canonical_field in assigned_canonical:
                    continue
                if clean_header in aliases:
                    matched_field = canonical_field
                    break
                # Partial contains
                for alias in aliases:
                    if alias == clean_header or (len(alias) > 3 and alias in clean_header):
                        matched_field = canonical_field
                        break
                if matched_field:
                    break

            if matched_field:
                mapping[header] = matched_field
                assigned_canonical.add(matched_field)

        return mapping
