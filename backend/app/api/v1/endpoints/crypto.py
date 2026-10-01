from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.crypto.models import BlockExplorerHelper
from app.services.crypto.service import CryptoReconciliationService

router = APIRouter()


class VerifyHashRequest(BaseModel):
    blockchain_network: str = Field("ETHEREUM", description="ETHEREUM, POLYGON, ARBITRUM, SOLANA, BITCOIN")
    transaction_hash: str = Field(..., description="On-chain transaction hash")


class CalculateGasRequest(BaseModel):
    blockchain_network: str = Field("ETHEREUM", description="ETHEREUM, POLYGON, ARBITRUM, SOLANA, BITCOIN")
    gas_units: int = Field(21000, description="Gas units consumed")
    gas_price_gwei: float = Field(25.0, description="Gas price in Gwei")
    native_usd_price: Optional[float] = Field(None, description="Optional override for native asset USD price")


class SlippageAnalysisRequest(BaseModel):
    expected_fiat_amount: float = Field(..., description="Invoice or agreed USD amount")
    actual_fiat_amount: float = Field(..., description="Actual on-chain settlement USD value")
    tolerance_percentage: float = Field(0.5, description="Allowed slippage percentage (default 0.5%)")


@router.get("/transactions", response_model=List[Dict[str, Any]])
def list_crypto_transactions(
    network: Optional[str] = Query(None, description="Optional network filter"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns enriched on-chain cryptocurrency and stablecoin transactions
    with verified block explorer URLs, gas costs in USD, and reconciliation statuses.
    """
    return CryptoReconciliationService.get_enriched_transactions(
        db=db, limit=limit, offset=offset, network=network
    )


@router.get("/wallets", response_model=List[Dict[str, Any]])
def list_treasury_wallets(
    db: Session = Depends(get_db),
):
    """
    Returns corporate treasury and counterparty wallet balances,
    linked master entities, and network block explorer links.
    """
    return CryptoReconciliationService.get_treasury_wallets(db=db)


@router.get("/analytics", response_model=Dict[str, Any])
def get_crypto_network_analytics(
    db: Session = Depends(get_db),
):
    """
    Returns on-chain volume, total gas expenditure in USD,
    and crypto reconciliation rates broken down by blockchain network.
    """
    return CryptoReconciliationService.get_network_analytics(db=db)


@router.post("/verify-hash", response_model=Dict[str, Any])
def verify_transaction_hash(
    req: VerifyHashRequest,
):
    """
    Validates on-chain transaction hash format and produces direct block explorer link.
    """
    net = req.blockchain_network.upper().strip()
    h = req.transaction_hash.strip()

    is_valid_format = False
    if net in ["ETHEREUM", "POLYGON", "ARBITRUM"]:
        is_valid_format = h.startswith("0x") and len(h) == 66
    elif net == "SOLANA":
        is_valid_format = len(h) >= 64 and len(h) <= 88
    elif net == "BITCOIN":
        is_valid_format = len(h) == 64

    explorer_url = BlockExplorerHelper.get_tx_url(net, h)

    return {
        "network": net,
        "transaction_hash": h,
        "is_valid_format": is_valid_format,
        "explorer_url": explorer_url,
    }


@router.post("/calculate-gas", response_model=Dict[str, Any])
def calculate_gas_cost(
    req: CalculateGasRequest,
):
    """
    Computes exact on-chain gas costs in native currency and fiat USD.
    """
    calc = CryptoReconciliationService.calculate_gas_fee(
        network=req.blockchain_network,
        gas_units=req.gas_units,
        gas_price_gwei=req.gas_price_gwei,
        native_usd_price=req.native_usd_price,
    )
    return calc.to_dict()


@router.post("/slippage-analysis", response_model=Dict[str, Any])
def analyze_exchange_slippage(
    req: SlippageAnalysisRequest,
):
    """
    Analyzes price variance and exchange slippage between invoice expectation and on-chain settlement.
    """
    res = CryptoReconciliationService.calculate_slippage(
        expected_fiat_amount=req.expected_fiat_amount,
        actual_fiat_amount=req.actual_fiat_amount,
        tolerance_percentage=req.tolerance_percentage,
    )
    return res.to_dict()
