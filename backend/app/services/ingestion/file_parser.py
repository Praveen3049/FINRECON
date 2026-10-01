import csv
import io
import json
from typing import List, Dict, Any, Tuple


class FileParser:
    @staticmethod
    def parse_file(content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Parses uploaded file content (CSV, JSON, XLSX) into a list of row dictionaries.
        Returns: (rows, detected_file_type)
        """
        lower_name = filename.lower()
        if lower_name.endswith(".csv"):
            return FileParser.parse_csv(content), "CSV"
        elif lower_name.endswith(".json"):
            return FileParser.parse_json(content), "JSON"
        elif lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            return FileParser.parse_excel(content), "XLSX"
        else:
            # Attempt JSON first, then CSV
            try:
                return FileParser.parse_json(content), "JSON"
            except Exception:
                return FileParser.parse_csv(content), "CSV"

    @staticmethod
    def parse_csv(content: bytes) -> List[Dict[str, Any]]:
        """Parses CSV bytes with utf-8-sig (handles UTF-8 BOM) and dialect detection."""
        text = content.decode("utf-8-sig", errors="replace")
        f = io.StringIO(text)
        
        # Sniff delimiter if possible, default to comma
        sample = text[:2048]
        delimiter = ","
        if "\t" in sample and sample.count("\t") > sample.count(","):
            delimiter = "\t"
        elif ";" in sample and sample.count(";") > sample.count(","):
            delimiter = ";"

        reader = csv.DictReader(f, delimiter=delimiter)
        rows = []
        for row in reader:
            # Clean keys and strip whitespace from values
            clean_row = {
                (k.strip() if k else f"col_{i}"): (v.strip() if isinstance(v, str) else v)
                for i, (k, v) in enumerate(row.items())
            }
            # Only add non-empty rows
            if any(clean_row.values()):
                rows.append(clean_row)
        return rows

    @staticmethod
    def parse_json(content: bytes) -> List[Dict[str, Any]]:
        """Parses JSON content supporting lists or wrapped objects."""
        text = content.decode("utf-8", errors="replace")
        data = json.loads(text)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Check for common array keys
            for key in ["transactions", "records", "data", "items", "invoices", "payments"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Single object wrapped in list
            return [data]
        raise ValueError("Invalid JSON format: expected list or object containing array of records")

    @staticmethod
    def parse_excel(content: bytes) -> List[Dict[str, Any]]:
        """Parses Excel XLSX using openpyxl."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
            sheet = wb.active
            rows_iter = sheet.iter_rows(values_only=True)
            headers = next(rows_iter, None)
            if not headers:
                return []
            
            clean_headers = [str(h).strip() if h is not None else f"col_{i}" for i, h in enumerate(headers)]
            records = []
            for row in rows_iter:
                if any(cell is not None for cell in row):
                    row_dict = {
                        clean_headers[i]: (str(cell).strip() if cell is not None else "")
                        for i, cell in enumerate(row) if i < len(clean_headers)
                    }
                    records.append(row_dict)
            return records
        except ImportError:
            raise ValueError("XLSX parsing requires openpyxl. Please upload CSV or JSON.")
