import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entity import Entity
from app.models.transaction import Transaction
from app.models.invoice import Invoice
from app.services.entity_resolution.models import (
    EntityResolutionQuery,
    EntityResolutionResult,
)
from app.services.entity_resolution.service import EntityResolutionService

router = APIRouter()


class CreateEntityRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    legal_name: Optional[str] = Field(None, max_length=200)
    entity_type: str = Field("CUSTOMER", description="CUSTOMER, VENDOR, PARTNER, INTERNAL")
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wallet_address: Optional[str] = None
    bank_account_number: Optional[str] = None


@router.post("/resolve", response_model=Dict[str, Any])
def resolve_entity(
    query: EntityResolutionQuery,
    db: Session = Depends(get_db),
):
    """
    Resolves multi-source financial and blockchain identity attributes (name, email,
    phone, tax ID, crypto wallet address) against registered corporate entities.
    Returns best match, confidence bucket (HIGH, MEDIUM, LOW), and full explainable evidence trail.
    """
    result = EntityResolutionService.resolve_query(query, db=db)
    return result.to_dict()


@router.get("", response_model=List[Dict[str, Any]])
def list_entities(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns list of all canonical entities registered in FinRecon with linked transaction counts.
    """
    return EntityResolutionService.get_all_entities_summary(db=db, limit=limit, offset=offset)


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_entity(
    req: CreateEntityRequest,
    db: Session = Depends(get_db),
):
    """
    Creates a new canonical corporate/individual entity.
    """
    new_entity = Entity(
        id=str(uuid.uuid4()),
        name=req.name,
        legal_name=req.legal_name,
        entity_type=req.entity_type.upper(),
        tax_id=req.tax_id,
        email=req.email,
        phone=req.phone,
        wallet_address=req.wallet_address,
        bank_account_number=req.bank_account_number,
    )
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)

    return {
        "id": new_entity.id,
        "name": new_entity.name,
        "legal_name": new_entity.legal_name,
        "entity_type": new_entity.entity_type,
        "tax_id": new_entity.tax_id,
        "email": new_entity.email,
        "wallet_address": new_entity.wallet_address,
        "created_at": new_entity.created_at.isoformat() if new_entity.created_at else None,
    }


@router.get("/{entity_id}", response_model=Dict[str, Any])
def get_entity_detail(
    entity_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves full profile of an entity including linked transactions and invoices.
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity '{entity_id}' not found.")

    txns = db.query(Transaction).filter(Transaction.entity_id == entity.id).limit(20).all()
    invs = db.query(Invoice).filter(Invoice.entity_id == entity.id).limit(20).all()

    return {
        "id": entity.id,
        "name": entity.name,
        "legal_name": entity.legal_name,
        "entity_type": entity.entity_type,
        "tax_id": entity.tax_id,
        "email": entity.email,
        "phone": entity.phone,
        "wallet_address": entity.wallet_address,
        "bank_account_number": entity.bank_account_number,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
        "transactions": [
            {
                "id": t.id,
                "transaction_id": getattr(t, "external_transaction_id", getattr(t, "transaction_id", t.id)),
                "amount": float(t.amount),
                "currency": t.currency,
                "direction": t.direction,
                "status": t.status,
                "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
            }
            for t in txns
        ],
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "total_amount": float(inv.total_amount),
                "currency": inv.currency,
                "status": inv.status,
                "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
            }
            for inv in invs
        ],
    }


@router.post("/{entity_id}/link-transaction/{transaction_id}", response_model=Dict[str, Any])
def link_transaction_to_entity(
    entity_id: str,
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """
    Manually or programmatically links a transaction to an entity.
    """
    txn = EntityResolutionService.link_transaction(db=db, transaction_id=transaction_id, entity_id=entity_id)
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' or Entity '{entity_id}' not found.",
        )

    return {
        "message": f"Transaction '{transaction_id}' successfully linked to Entity '{entity_id}'",
        "transaction_id": getattr(txn, "external_transaction_id", txn.id),
        "entity_id": txn.entity_id,
    }
