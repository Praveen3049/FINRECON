from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services.normalization.normalizer import NormalizationEngine
from app.services.normalization.models import NormalizedField, NormalizedRecord

router = APIRouter()


class FieldNormalizationRequest(BaseModel):
    field_type: str = Field(..., description="One of: name, company_name, wallet_address, transaction_id, invoice_id, amount, currency, date, timestamp, payment_reference")
    value: Any = Field(..., description="Raw value to normalize")


class RecordNormalizationRequest(BaseModel):
    record: Dict[str, Any] = Field(..., description="Dictionary representing raw source record row")
    record_type: str = Field("TRANSACTION", description="TRANSACTION, INVOICE, CRYPTO, etc.")


class BatchNormalizationRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(..., description="List of raw source records")
    record_type: str = Field("TRANSACTION", description="TRANSACTION, INVOICE, CRYPTO, etc.")


@router.post("/field", response_model=Dict[str, Any])
def normalize_field(req: FieldNormalizationRequest):
    """
    Normalizes a single field value according to its designated field type.
    Always returns both original_value and normalized_value with validation metadata.
    """
    ft = req.field_type.lower().strip()
    val = req.value

    if ft == "name":
        result = NormalizationEngine.normalize_name(val)
    elif ft in ["company", "company_name", "entity_name"]:
        result = NormalizationEngine.normalize_company_name(val)
    elif ft in ["wallet", "wallet_address", "crypto_address"]:
        result = NormalizationEngine.normalize_wallet_address(val)
    elif ft in ["transaction_id", "txn_id"]:
        result = NormalizationEngine.normalize_transaction_id(val)
    elif ft in ["invoice_id", "invoice_number"]:
        result = NormalizationEngine.normalize_invoice_id(val)
    elif ft in ["amount", "fee"]:
        result = NormalizationEngine.normalize_amount(val)
    elif ft in ["currency", "ccy"]:
        result = NormalizationEngine.normalize_currency(val)
    elif ft == "date":
        result = NormalizationEngine.normalize_date(val)
    elif ft in ["timestamp", "datetime"]:
        result = NormalizationEngine.normalize_timestamp(val)
    elif ft in ["payment_reference", "reference", "utr"]:
        result = NormalizationEngine.normalize_payment_reference(val)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported field_type '{req.field_type}'. Supported: name, company_name, wallet_address, transaction_id, invoice_id, amount, currency, date, timestamp, payment_reference"
        )

    return result.to_dict()


@router.post("/record", response_model=Dict[str, Any])
def normalize_record(req: RecordNormalizationRequest):
    """
    Normalizes an entire row/record, mapping canonical financial fields
    while preserving original values and recording any schema warnings.
    """
    normalized_rec = NormalizationEngine.normalize_record(req.record, record_type=req.record_type)
    return {
        "record_type": normalized_rec.record_type,
        "all_valid": normalized_rec.all_valid,
        "warnings": normalized_rec.warnings,
        "fields": {k: f.to_dict() for k, f in normalized_rec.fields.items()},
    }


@router.post("/batch", response_model=Dict[str, Any])
def normalize_batch(req: BatchNormalizationRequest):
    """
    Normalizes a batch of records. Useful for testing batch pipelines and dataset ingestion.
    """
    results = []
    total_valid = 0
    total_records = len(req.records)

    for rec in req.records:
        norm = NormalizationEngine.normalize_record(rec, record_type=req.record_type)
        if norm.all_valid:
            total_valid += 1
        results.append({
            "record_type": norm.record_type,
            "all_valid": norm.all_valid,
            "fields": {k: f.to_dict() for k, f in norm.fields.items()},
        })

    return {
        "total_records": total_records,
        "total_valid": total_valid,
        "valid_percentage": round((total_valid / total_records * 100), 2) if total_records > 0 else 0.0,
        "records": results,
    }
