from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Optional, Tuple
from app.services.normalization.models import NormalizedField, NormalizedRecord


class NormalizationEngine:
    # Company suffix mapping to standard canonical tokens
    COMPANY_SUFFIX_MAP = {
        "ltd": "ltd",
        "limited": "ltd",
        "inc": "inc",
        "incorporated": "inc",
        "corp": "corp",
        "corporation": "corp",
        "llc": "llc",
        "l.l.c.": "llc",
        "co": "co",
        "company": "co",
        "pvt": "pvt",
        "private": "pvt",
        "plc": "plc",
        "gmbh": "gmbh",
        "sa": "sa",
        "llp": "llp",
        "lp": "lp",
    }

    # Currency symbol to ISO code mapping
    CURRENCY_MAP = {
        "$": "USD",
        "usd": "USD",
        "us dollar": "USD",
        "us dollars": "USD",
        "₹": "INR",
        "inr": "INR",
        "rs": "INR",
        "rupee": "INR",
        "rupees": "INR",
        "€": "EUR",
        "eur": "EUR",
        "euro": "EUR",
        "euros": "EUR",
        "£": "GBP",
        "gbp": "GBP",
        "pound": "GBP",
        "pounds": "GBP",
        "¥": "JPY",
        "jpy": "JPY",
        "yen": "JPY",
        "c$": "CAD",
        "cad": "CAD",
        "a$": "AUD",
        "aud": "AUD",
        "usdt": "USDT",
        "tether": "USDT",
        "usdc": "USDC",
        "usd coin": "USDC",
        "eth": "ETH",
        "ether": "ETH",
        "ethereum": "ETH",
        "btc": "BTC",
        "bitcoin": "BTC",
        "matic": "MATIC",
        "polygon": "MATIC",
        "sol": "SOL",
        "solana": "SOL",
    }

    # 1. Names
    @classmethod
    def normalize_name(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="name",
                original_value=original,
                normalized_value="",
                field_type="name",
                is_valid=False,
                error_message="Name is empty",
            )

        s = str(value).strip()
        # Handle "Last, First" format
        if "," in s:
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if len(parts) == 2:
                s = f"{parts[1]} {parts[0]}"

        # Remove honorifics
        s = re.sub(r"^(mr\.|mrs\.|ms\.|dr\.|prof\.)\s+", "", s, flags=re.IGNORECASE)
        # Clean extra spaces
        s = re.sub(r"\s+", " ", s).strip()
        # Standardize capitalization
        normalized = s.title()

        return NormalizedField(
            field_name="name",
            original_value=original,
            normalized_value=normalized,
            field_type="name",
            is_valid=True,
            metadata={"clean_lower": normalized.lower()},
        )

    # 2. Company Names
    @classmethod
    def normalize_company_name(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="company_name",
                original_value=original,
                normalized_value="",
                field_type="company_name",
                is_valid=False,
                error_message="Company name is empty",
            )

        s = str(value).strip().lower()
        # Strip trailing dots, commas, quotes
        s = re.sub(r"[\.,'\"\-]+$", "", s).strip()
        # Remove internal punctuation like periods in L.L.C. or LTD.
        s = s.replace(".", "").replace(",", "")
        
        words = s.split()
        if not words:
            return NormalizedField(
                field_name="company_name",
                original_value=original,
                normalized_value="",
                field_type="company_name",
                is_valid=False,
            )

        # Check and normalize suffix
        base_words = []
        suffix_token: Optional[str] = None

        for w in words:
            clean_w = w.strip()
            if clean_w in cls.COMPANY_SUFFIX_MAP:
                suffix_token = cls.COMPANY_SUFFIX_MAP[clean_w]
            else:
                base_words.append(clean_w)

        base_name = " ".join(base_words).strip()
        if suffix_token:
            normalized = f"{base_name} {suffix_token}".strip()
        else:
            normalized = base_name

        return NormalizedField(
            field_name="company_name",
            original_value=original,
            normalized_value=normalized,
            field_type="company_name",
            is_valid=True,
            metadata={
                "base_name": base_name,
                "detected_suffix": suffix_token,
            },
        )

    # 3. Wallet Addresses
    @classmethod
    def normalize_wallet_address(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="wallet_address",
                original_value=original,
                normalized_value=None,
                field_type="wallet_address",
                is_valid=False,
                error_message="Wallet address is empty",
            )

        s = str(value).strip()
        # EVM address (0x + 40 hex chars)
        evm_match = re.match(r"^0x[a-fA-F0-9]{40}$", s)
        if evm_match:
            normalized = s.lower()
            return NormalizedField(
                field_name="wallet_address",
                original_value=original,
                normalized_value=normalized,
                field_type="wallet_address",
                is_valid=True,
                metadata={"network_type": "EVM", "length": 42},
            )

        # Solana (Base58 32-44 chars) or Bitcoin (1, 3, or bc1)
        if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", s):
            return NormalizedField(
                field_name="wallet_address",
                original_value=original,
                normalized_value=s,
                field_type="wallet_address",
                is_valid=True,
                metadata={"network_type": "SOLANA_OR_BITCOIN", "length": len(s)},
            )

        # Bitcoin Bech32 (bc1...)
        if s.lower().startswith("bc1") and len(s) >= 42:
            return NormalizedField(
                field_name="wallet_address",
                original_value=original,
                normalized_value=s.lower(),
                field_type="wallet_address",
                is_valid=True,
                metadata={"network_type": "BITCOIN_BECH32", "length": len(s)},
            )

        return NormalizedField(
            field_name="wallet_address",
            original_value=original,
            normalized_value=s,
            field_type="wallet_address",
            is_valid=False,
            error_message="Unrecognized blockchain wallet address format",
        )

    # 4. Transaction IDs
    @classmethod
    def normalize_transaction_id(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="transaction_id",
                original_value=original,
                normalized_value="",
                field_type="transaction_id",
                is_valid=False,
                error_message="Transaction ID is empty",
            )

        s = str(value).strip().strip("#").strip()
        # Replace slashes, underscores with hyphens
        s = re.sub(r"[\s_/\\]+", "-", s)
        normalized = s.upper()

        return NormalizedField(
            field_name="transaction_id",
            original_value=original,
            normalized_value=normalized,
            field_type="transaction_id",
            is_valid=True,
        )

    # 5. Invoice IDs
    @classmethod
    def normalize_invoice_id(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="invoice_id",
                original_value=original,
                normalized_value="",
                field_type="invoice_id",
                is_valid=False,
                error_message="Invoice ID is empty",
            )

        s = str(value).strip()
        # Strip prefixes like "Invoice:", "Inv #", "Invoice No."
        s = re.sub(r"^(invoice\s*(no\.?|#|id)?|inv\s*(no\.?|#|id)?)\s*[:\-]?\s*", "", s, flags=re.IGNORECASE)
        # Normalize slashes and spaces to hyphens
        s = re.sub(r"[\s_/\\]+", "-", s.strip())
        normalized = s.upper()
        if not normalized.startswith("INV-") and not normalized.startswith("INV"):
            normalized = f"INV-{normalized}"

        return NormalizedField(
            field_name="invoice_id",
            original_value=original,
            normalized_value=normalized,
            field_type="invoice_id",
            is_valid=True,
        )

    # 6. Amounts
    @classmethod
    def normalize_amount(cls, value: Any) -> NormalizedField[float]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="amount",
                original_value=original,
                normalized_value=0.0,
                field_type="amount",
                is_valid=False,
                error_message="Amount is empty",
            )

        if isinstance(value, (int, float, Decimal)):
            d = Decimal(str(value))
            is_debit = d < 0
            abs_val = abs(d)
            return NormalizedField(
                field_name="amount",
                original_value=original,
                normalized_value=float(abs_val),
                field_type="amount",
                is_valid=True,
                metadata={
                    "decimal": str(abs_val),
                    "direction": "DEBIT" if is_debit else "CREDIT",
                },
            )

        s = str(value).strip()
        # Check negative parentheses (e.g. "(50,000.00)")
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1].strip()
        elif "-" in s:
            is_negative = True
            s = s.replace("-", "").strip()

        # Handle European decimal comma: "49.500,00" vs American "49,500.00"
        if "," in s and "." in s:
            if s.rfind(",") > s.rfind("."):
                # European: 49.500,00 -> 49500.00
                s = s.replace(".", "").replace(",", ".")
            else:
                # American: 49,500.00 -> 49500.00
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            # Check if comma is decimal or thousands
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 2:
                # 50,00 -> 50.00
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")

        # Strip remaining non-numeric except decimal point
        cleaned_num = re.sub(r"[^\d.]", "", s)
        try:
            dec = Decimal(cleaned_num)
            direction = "DEBIT" if is_negative else "CREDIT"
            return NormalizedField(
                field_name="amount",
                original_value=original,
                normalized_value=float(dec),
                field_type="amount",
                is_valid=True,
                metadata={
                    "decimal": str(dec),
                    "direction": direction,
                },
            )
        except (InvalidOperation, ValueError) as e:
            return NormalizedField(
                field_name="amount",
                original_value=original,
                normalized_value=0.0,
                field_type="amount",
                is_valid=False,
                error_message=f"Invalid numeric amount format: {e}",
            )

    # 7. Currency
    @classmethod
    def normalize_currency(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="currency",
                original_value=original,
                normalized_value="USD",
                field_type="currency",
                is_valid=True,
                metadata={"defaulted": True},
            )

        s = str(value).strip().lower()
        if s in cls.CURRENCY_MAP:
            normalized = cls.CURRENCY_MAP[s]
            return NormalizedField(
                field_name="currency",
                original_value=original,
                normalized_value=normalized,
                field_type="currency",
                is_valid=True,
            )

        # Standard 3-letter code fallback
        clean_code = re.sub(r"[^a-zA-Z]", "", s).upper()
        if len(clean_code) == 3:
            return NormalizedField(
                field_name="currency",
                original_value=original,
                normalized_value=clean_code,
                field_type="currency",
                is_valid=True,
            )

        return NormalizedField(
            field_name="currency",
            original_value=original,
            normalized_value="USD",
            field_type="currency",
            is_valid=False,
            error_message=f"Unrecognized currency: {value}",
        )

    # 8. Dates
    @classmethod
    def normalize_date(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="date",
                original_value=original,
                normalized_value=date.today().isoformat(),
                field_type="date",
                is_valid=False,
                error_message="Date is empty",
            )

        if isinstance(value, datetime):
            d_str = value.date().isoformat()
            return NormalizedField(
                field_name="date",
                original_value=original,
                normalized_value=d_str,
                field_type="date",
                is_valid=True,
            )
        if isinstance(value, date):
            return NormalizedField(
                field_name="date",
                original_value=original,
                normalized_value=value.isoformat(),
                field_type="date",
                is_valid=True,
            )

        s = str(value).strip()
        # ISO format YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}", s):
            clean_date = s[:10]
            try:
                datetime.strptime(clean_date, "%Y-%m-%d")
                return NormalizedField(
                    field_name="date",
                    original_value=original,
                    normalized_value=clean_date,
                    field_type="date",
                    is_valid=True,
                )
            except ValueError:
                pass

        # Parse formats with day vs month resolution
        formats = [
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%d-%b-%Y",  # 29-Sep-2026
            "%d %b %Y",  # 29 Sep 2026
            "%b %d, %Y", # Sep 29, 2026
            "%Y/%m/%d",
        ]

        # Check unambiguous DD/MM/YYYY (where first part > 12)
        match_slash = re.match(r"^(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})", s)
        if match_slash:
            p1, p2, yr = int(match_slash.group(1)), int(match_slash.group(2)), int(match_slash.group(3))
            if p1 > 12 and p2 <= 12:
                # Must be DD/MM/YYYY
                d_obj = date(yr, p2, p1)
                return NormalizedField(
                    field_name="date",
                    original_value=original,
                    normalized_value=d_obj.isoformat(),
                    field_type="date",
                    is_valid=True,
                )
            elif p2 > 12 and p1 <= 12:
                # Must be MM/DD/YYYY
                d_obj = date(yr, p1, p2)
                return NormalizedField(
                    field_name="date",
                    original_value=original,
                    normalized_value=d_obj.isoformat(),
                    field_type="date",
                    is_valid=True,
                )

        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                return NormalizedField(
                    field_name="date",
                    original_value=original,
                    normalized_value=dt.date().isoformat(),
                    field_type="date",
                    is_valid=True,
                )
            except ValueError:
                continue

        return NormalizedField(
            field_name="date",
            original_value=original,
            normalized_value=date.today().isoformat(),
            field_type="date",
            is_valid=False,
            error_message=f"Unable to parse date string: {value}",
        )

    # 9. Timestamps
    @classmethod
    def normalize_timestamp(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="timestamp",
                original_value=original,
                normalized_value=datetime.now(timezone.utc).isoformat(),
                field_type="timestamp",
                is_valid=False,
                error_message="Timestamp is empty",
            )

        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            utc_iso = value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return NormalizedField(
                field_name="timestamp",
                original_value=original,
                normalized_value=utc_iso,
                field_type="timestamp",
                is_valid=True,
            )

        s = str(value).strip()
        # UNIX epoch seconds (10 digits) or milliseconds (13 digits)
        if re.match(r"^\d{10}(\.\d+)?$", s):
            dt = datetime.fromtimestamp(float(s), tz=timezone.utc)
            return NormalizedField(
                field_name="timestamp",
                original_value=original,
                normalized_value=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                field_type="timestamp",
                is_valid=True,
            )
        elif re.match(r"^\d{13}$", s):
            dt = datetime.fromtimestamp(float(s) / 1000.0, tz=timezone.utc)
            return NormalizedField(
                field_name="timestamp",
                original_value=original,
                normalized_value=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                field_type="timestamp",
                is_valid=True,
            )

        # ISO format parser
        iso_formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in iso_formats:
            try:
                dt = datetime.strptime(s, fmt)
                dt = dt.replace(tzinfo=timezone.utc)
                return NormalizedField(
                    field_name="timestamp",
                    original_value=original,
                    normalized_value=dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    field_type="timestamp",
                    is_valid=True,
                )
            except ValueError:
                continue

        # Fallback date only
        date_res = cls.normalize_date(value)
        if date_res.is_valid and date_res.normalized_value:
            iso_ts = f"{date_res.normalized_value}T00:00:00Z"
            return NormalizedField(
                field_name="timestamp",
                original_value=original,
                normalized_value=iso_ts,
                field_type="timestamp",
                is_valid=True,
                metadata={"time_defaulted": True},
            )

        return NormalizedField(
            field_name="timestamp",
            original_value=original,
            normalized_value=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            field_type="timestamp",
            is_valid=False,
            error_message=f"Unable to parse timestamp: {value}",
        )

    # 10. Payment References
    @classmethod
    def normalize_payment_reference(cls, value: Any) -> NormalizedField[str]:
        original = value
        if value is None or str(value).strip() == "":
            return NormalizedField(
                field_name="payment_reference",
                original_value=original,
                normalized_value="",
                field_type="payment_reference",
                is_valid=False,
                error_message="Payment reference is empty",
            )

        s = str(value).strip()
        # Remove common prefixes: "Ref:", "Reference #", "UTR:", "Check #"
        s = re.sub(r"^(ref(erence)?\s*(#|no\.?|id)?|utr|chk|check\s*(#|no\.?)?)\s*[:\-]?\s*", "", s, flags=re.IGNORECASE)
        # Normalize spaces and slashes to hyphens
        s = re.sub(r"[\s_/\\]+", "-", s.strip())
        normalized = s.upper()

        return NormalizedField(
            field_name="payment_reference",
            original_value=original,
            normalized_value=normalized,
            field_type="payment_reference",
            is_valid=True,
        )

    # Complete Record Normalization
    @classmethod
    def normalize_record(cls, record_dict: Dict[str, Any], record_type: str = "TRANSACTION") -> NormalizedRecord:
        """
        Normalizes an entire record dictionary into a canonical representation
        while preserving all original values.
        """
        normalized_record = NormalizedRecord(record_type=record_type)
        warnings = []

        for key, val in record_dict.items():
            clean_key = key.lower().strip()

            if clean_key in ["counterparty", "counterparty_name", "entity_name", "customer_name", "vendor_name"]:
                # Check if individual name or company name
                if any(suffix in str(val).lower() for suffix in cls.COMPANY_SUFFIX_MAP):
                    field_res = cls.normalize_company_name(val)
                else:
                    field_res = cls.normalize_name(val)
                field_res.field_name = "counterparty"
                normalized_record.fields["counterparty"] = field_res

            elif clean_key in ["amount", "gross_amount", "total", "total_amount", "debit", "credit"]:
                field_res = cls.normalize_amount(val)
                field_res.field_name = "amount"
                normalized_record.fields["amount"] = field_res

            elif clean_key in ["fee", "fee_amount", "processing_fee"]:
                field_res = cls.normalize_amount(val)
                field_res.field_name = "fee_amount"
                normalized_record.fields["fee_amount"] = field_res

            elif clean_key in ["currency", "curr", "ccy"]:
                field_res = cls.normalize_currency(val)
                field_res.field_name = "currency"
                normalized_record.fields["currency"] = field_res

            elif clean_key in ["date", "transaction_date", "txn_date", "issue_date"]:
                field_res = cls.normalize_date(val)
                field_res.field_name = "transaction_date"
                normalized_record.fields["transaction_date"] = field_res

            elif clean_key in ["timestamp", "transaction_timestamp", "created", "created_at"]:
                field_res = cls.normalize_timestamp(val)
                field_res.field_name = "transaction_timestamp"
                normalized_record.fields["transaction_timestamp"] = field_res

            elif clean_key in ["wallet_address", "wallet_from", "wallet_to", "sender", "recipient"]:
                field_res = cls.normalize_wallet_address(val)
                field_res.field_name = clean_key
                normalized_record.fields[clean_key] = field_res

            elif clean_key in ["transaction_id", "txn_id", "charge_id", "journal_id"]:
                field_res = cls.normalize_transaction_id(val)
                field_res.field_name = "transaction_id"
                normalized_record.fields["transaction_id"] = field_res

            elif clean_key in ["invoice_id", "invoice_number", "inv_number"]:
                field_res = cls.normalize_invoice_id(val)
                field_res.field_name = "invoice_id"
                normalized_record.fields["invoice_id"] = field_res

            elif clean_key in ["reference_number", "reference", "ref_number", "utr", "payment_reference"]:
                field_res = cls.normalize_payment_reference(val)
                field_res.field_name = "payment_reference"
                normalized_record.fields["payment_reference"] = field_res

            else:
                # Passthrough field
                normalized_record.fields[clean_key] = NormalizedField(
                    field_name=clean_key,
                    original_value=val,
                    normalized_value=val,
                    field_type="passthrough",
                    is_valid=True,
                )

        # Check overall validity
        all_valid = all(f.is_valid for f in normalized_record.fields.values())
        normalized_record.all_valid = all_valid
        normalized_record.warnings = warnings
        return normalized_record
