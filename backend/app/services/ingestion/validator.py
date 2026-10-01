from datetime import datetime, date
from decimal import Decimal
import re
from typing import Dict, Any, Tuple, Optional, List


class RowValidator:
    @staticmethod
    def parse_amount(val: Any) -> Tuple[Decimal, str]:
        """
        Parses numeric amounts from string or numeric input, stripping currency symbols and commas.
        Returns: (abs_amount, direction)
        """
        if val is None or val == "":
            return Decimal("0.00"), "CREDIT"
        
        if isinstance(val, (int, float, Decimal)):
            num = Decimal(str(val))
            direction = "DEBIT" if num < 0 else "CREDIT"
            return abs(num), direction

        s = str(val).strip()
        # Check negative signs or parentheses
        is_negative = False
        if s.startswith("(") and s.endswith(")"):
            is_negative = True
            s = s[1:-1]
        elif "-" in s:
            is_negative = True
            s = s.replace("-", "")

        # Remove currency symbols and whitespace
        s = re.sub(r"[^\d.]", "", s)
        try:
            num = Decimal(s) if s else Decimal("0.00")
            direction = "DEBIT" if is_negative else "CREDIT"
            return num, direction
        except Exception:
            return Decimal("0.00"), "CREDIT"

    @staticmethod
    def parse_date(val: Any) -> Tuple[date, Optional[datetime]]:
        """
        Parses dates and timestamps from multiple date format strings.
        Returns: (parsed_date, parsed_datetime)
        """
        if val is None or val == "":
            d = date.today()
            return d, None

        if isinstance(val, datetime):
            return val.date(), val
        if isinstance(val, date):
            return val, None

        s = str(val).strip()
        # Common formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.date(), dt
            except ValueError:
                continue

        # Fallback to current date
        return date.today(), None

    @staticmethod
    def validate_crypto_row(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates that essential crypto transaction fields exist."""
        errors = []
        tx_hash = row.get("transaction_hash") or row.get("tx_hash") or row.get("hash")
        if not tx_hash:
            errors.append("Missing transaction_hash")
        elif not str(tx_hash).startswith("0x") and len(str(tx_hash)) < 32:
            errors.append(f"Invalid transaction hash format: {tx_hash}")

        if not (row.get("wallet_to") or row.get("to")):
            errors.append("Missing destination wallet address")

        return len(errors) == 0, errors
