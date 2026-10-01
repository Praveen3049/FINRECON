import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.deps import require_role, get_optional_user
from app.models.user import User, UserRole
from app.models import DataSource, Transaction, Invoice, CryptoTransaction
from app.services.ingestion.ingestion_service import IngestionService

router = APIRouter()

# Path to sample datasets
SAMPLE_DATASETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../../datasets")
)


class CreateAccountRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    source_type: str = Field("BANK", description="BANK, PAYMENT_GATEWAY, ACCOUNTING, INVOICE, CRYPTO")
    account_identifier: Optional[str] = Field(None, max_length=100)
    currency: str = Field("INR", max_length=3)
    file_format: Optional[str] = Field("CSV", max_length=10)


@router.post("/accounts", status_code=status.HTTP_201_CREATED, tags=["Ingestion"])
def create_account(
    request: CreateAccountRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    Creates a new user-managed financial account / data source.
    """
    account_id = str(uuid.uuid4())
    clean_identifier = request.account_identifier.strip() if request.account_identifier else f"ACC-{uuid.uuid4().hex[:8].upper()}"
    account = DataSource(
        id=account_id,
        name=request.name.strip(),
        source_type=request.source_type.upper(),
        file_format=request.file_format.upper() if request.file_format else "CSV",
        account_identifier=clean_identifier,
        currency=request.currency.upper(),
        owner_id=user.id if user else None,
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return {
        "status": "success",
        "message": f"Account '{account.name}' created successfully",
        "account": {
            "id": account.id,
            "name": account.name,
            "source_type": account.source_type,
            "file_format": account.file_format,
            "account_identifier": account.account_identifier,
            "currency": account.currency,
            "records_count": 0,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat(),
        }
    }


@router.get("/accounts", status_code=status.HTTP_200_OK, tags=["Ingestion"])
def list_accounts(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> List[Dict[str, Any]]:
    """
    Returns accounts for the current user (if regular user) or all accounts (if manager/anonymous).
    """
    query = db.query(DataSource)
    if user and user.role == UserRole.USER:
        user_accounts = query.filter(DataSource.owner_id == user.id).all()
        sources = user_accounts if len(user_accounts) > 0 else query.limit(6).all()
    else:
        sources = query.all()

    results = []
    for s in sources:
        if s.source_type == "CRYPTO":
            count = db.query(CryptoTransaction).filter_by(source_id=s.id).count()
        else:
            count = db.query(Transaction).filter_by(source_id=s.id).count()

        results.append({
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "file_format": s.file_format,
            "account_identifier": s.account_identifier,
            "currency": s.currency,
            "is_active": s.is_active,
            "records_count": count,
            "owner_id": s.owner_id,
            "created_at": s.created_at.isoformat(),
        })
    return results


@router.delete("/accounts/{account_id}", status_code=status.HTTP_200_OK, tags=["Ingestion"])
def delete_account(
    account_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    Deletes a user-managed account and its associated records.
    """
    account = db.query(DataSource).filter_by(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if user and user.role != UserRole.MANAGER and account.owner_id and account.owner_id != user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this account")

    db.delete(account)
    db.commit()
    return {"status": "success", "message": f"Account '{account.name}' deleted successfully"}


@router.post("/upload", status_code=status.HTTP_201_CREATED, tags=["Ingestion"])
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    source_name: Optional[str] = Form(None),
    account_id: Optional[str] = Form(None),
    account_identifier: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    Ingests and validates multi-source financial and crypto files (CSV, JSON, XLSX).
    Detects headers, normalizes fields to canonical schema, and stores records.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        owner_id = user.id if user else None
        summary = IngestionService.process_file_upload(
            db=db,
            content=content,
            filename=file.filename or "upload.csv",
            source_type=source_type,
            source_name=source_name,
            account_id=account_id,
            account_identifier=account_identifier,
            owner_id=owner_id,
        )
        return {
            "status": "success",
            "message": f"Successfully ingested {summary['processed_records']} of {summary['total_records']} records",
            "summary": summary
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion processing error: {str(e)}")


@router.get("/sources", status_code=status.HTTP_200_OK, tags=["Ingestion"])
def list_data_sources(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Lists all configured data sources and their current transaction volumes."""
    sources = db.query(DataSource).all()
    results = []
    for s in sources:
        if s.source_type == "CRYPTO":
            count = db.query(CryptoTransaction).filter_by(source_id=s.id).count()
        else:
            count = db.query(Transaction).filter_by(source_id=s.id).count()

        results.append({
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "file_format": s.file_format,
            "account_identifier": s.account_identifier,
            "currency": s.currency,
            "is_active": s.is_active,
            "records_count": count,
            "created_at": s.created_at.isoformat(),
        })
    return results


@router.get("/sample/{source_type}", tags=["Ingestion"])
def download_sample_dataset(source_type: str):
    """Provides downloadable sample dataset templates for any of the 5 financial sources."""
    from fastapi.responses import Response
    source_type = source_type.upper()
    file_map = {
        "BANK": ("bank_statement_sample.csv", "text/csv", "transaction_date,amount,currency,direction,reference_number,counterparty_name,description\n2026-09-29,289088.20,INR,CREDIT,SBINR41094041204,Anand Motors Ltd,RTGS Settlement\n"),
        "PAYMENT_GATEWAY": ("payment_gateway_sample.json", "application/json", '[\n  {"payment_number": "PAY-10-0297", "amount": 289088.20, "currency": "INR", "reference": "SBINR41094041204", "payment_date": "2026-09-29", "client_name": "Anand Motors Ltd"}\n]\n'),
        "ACCOUNTING": ("accounting_records_sample.csv", "text/csv", "entry_date,account_number,account_name,debit,credit,currency,reference,description\n2026-09-29,1200,Accounts Receivable,0.00,289088.20,INR,PAY-10-0297,Client Remittance Clearance\n"),
        "INVOICE": ("invoices_sample.csv", "text/csv", "invoice_number,issue_date,due_date,total_amount,currency,recipient_name,status\nINV-10-0211,2026-09-20,2026-10-20,289088.20,INR,Anand Motors Ltd,PAID\n"),
        "CRYPTO": ("crypto_transactions_sample.json", "application/json", '[\n  {"blockchain_network": "ETHEREUM", "transaction_hash": "0x4a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b", "wallet_from": "0x71C80915E33366b90c485657519EF4e1", "wallet_to": "0x29D7d1dd5B6f9C864d9db560D72a247c178a836B", "asset": "USDT", "token_amount": 10000.0, "fiat_value": 10000.0, "gas_fee_fiat": 2.50}\n]\n'),
    }
    if source_type not in file_map:
        raise HTTPException(status_code=404, detail=f"No sample available for source: {source_type}")

    filename, media_type, sample_content = file_map[source_type]
    file_path = os.path.join(SAMPLE_DATASETS_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type=media_type, filename=filename)

    return Response(
        content=sample_content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/sync-aczen", status_code=status.HTTP_200_OK, tags=["Ingestion"])
async def sync_aczen_data(
    purge_old_data: bool = True,
    db: Session = Depends(get_db),
    _user: Optional[User] = Depends(require_role(UserRole.MANAGER)),
) -> Dict[str, Any]:
    """
    Triggers live synchronization with official Aczen Nova accounting books:
    Clients, Vendors, Invoices, Payments, and Bank Transactions.
    Purges synthetic demo datasets and executes 7-pass deterministic reconciliation.
    """
    try:
        from app.services.ingestion.aczen_sync import AczenNovaSyncService
        result = await AczenNovaSyncService.sync_and_replace_with_aczen_data(
            db=db,
            purge_old_data=purge_old_data
        )
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Aczen sync error: {str(e)}")


@router.get("/aczen-status", status_code=status.HTTP_200_OK, tags=["Ingestion"])
def get_aczen_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns status of Aczen Nova API connectivity and current record volumes in the system.
    """
    from app.core.config import settings
    from app.models import Transaction, Invoice, Entity, ReconciliationCase, DiscrepancyRecord

    is_configured = bool(settings.NOVA_API_KEY and settings.NOVA_API_KEY.strip())
    txns_count = db.query(Transaction).count()
    invoices_count = db.query(Invoice).count()
    entities_count = db.query(Entity).count()
    cases_count = db.query(ReconciliationCase).count()
    discrepancies_count = db.query(DiscrepancyRecord).count()

    return {
        "nova_configured": is_configured,
        "base_url": settings.NOVA_API_BASE_URL,
        "records": {
            "transactions": txns_count,
            "invoices": invoices_count,
            "entities": entities_count,
            "reconciliation_cases": cases_count,
            "discrepancies": discrepancies_count,
        }
    }

