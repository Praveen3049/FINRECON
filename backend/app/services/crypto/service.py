from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.crypto_transaction import CryptoTransaction
from app.models.entity import Entity
from app.models.invoice import Invoice
from app.models.reconciliation_match import ReconciliationMatch
from app.services.crypto.models import (
    BlockExplorerHelper,
    GasFeeCalculation,
    SlippageAnalysis,
    WalletTreasurySummary,
)


class CryptoReconciliationService:
    """
    Enterprise crypto-to-fiat ledger reconciliation service.
    Handles gas fee separation, price slippage calculations,
    block explorer verification links, and treasury wallet aggregation.
    """

    NATIVE_ASSET_MAP = {
        "ETHEREUM": {"token": "ETH", "default_price": 2450.0},
        "POLYGON": {"token": "MATIC", "default_price": 0.42},
        "ARBITRUM": {"token": "ETH", "default_price": 2450.0},
        "SOLANA": {"token": "SOL", "default_price": 145.0},
        "BITCOIN": {"token": "BTC", "default_price": 64000.0},
    }

    @classmethod
    def calculate_gas_fee(
        cls,
        network: str,
        gas_units: int,
        gas_price_gwei: float,
        native_usd_price: Optional[float] = None,
    ) -> GasFeeCalculation:
        net = network.upper().strip()
        meta = cls.NATIVE_ASSET_MAP.get(net, {"token": "ETH", "default_price": 2450.0})
        usd_price = native_usd_price if native_usd_price is not None else meta["default_price"]

        gas_fee_native = float(Decimal(str(gas_units)) * Decimal(str(gas_price_gwei)) * Decimal("0.000000001"))
        gas_fee_usd = gas_fee_native * usd_price

        return GasFeeCalculation(
            network=net,
            native_token=meta["token"],
            gas_units=gas_units,
            gas_price_gwei=gas_price_gwei,
            gas_fee_native=gas_fee_native,
            native_usd_price=usd_price,
            gas_fee_usd=gas_fee_usd,
        )

    @classmethod
    def calculate_slippage(
        cls,
        expected_fiat_amount: float,
        actual_fiat_amount: float,
        tolerance_percentage: float = 0.5,
    ) -> SlippageAnalysis:
        diff = actual_fiat_amount - expected_fiat_amount
        pct = (abs(diff) / max(0.01, expected_fiat_amount)) * 100.0
        acceptable = pct <= tolerance_percentage

        notes = (
            f"Slippage within acceptable boundary ({pct:.2f}% <= {tolerance_percentage}%)"
            if acceptable
            else f"Slippage exceeds threshold ({pct:.2f}% > {tolerance_percentage}%). Review root cause."
        )

        return SlippageAnalysis(
            expected_fiat_amount=expected_fiat_amount,
            actual_fiat_amount=actual_fiat_amount,
            slippage_usd=diff,
            slippage_percentage=pct,
            tolerance_percentage=tolerance_percentage,
            is_acceptable=acceptable,
            notes=notes,
        )

    @classmethod
    def get_enriched_transactions(
        cls,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        network: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        q = db.query(CryptoTransaction)
        if network:
            q = q.filter(CryptoTransaction.blockchain_network == network.upper())

        txns = q.order_by(CryptoTransaction.transaction_timestamp.desc()).offset(offset).limit(limit).all()
        results = []

        for t in txns:
            net = t.blockchain_network
            tx_url = BlockExplorerHelper.get_tx_url(net, t.transaction_hash)
            from_url = BlockExplorerHelper.get_address_url(net, t.wallet_from)
            to_url = BlockExplorerHelper.get_address_url(net, t.wallet_to)

            # Check matching status in ReconciliationMatch
            match = db.query(ReconciliationMatch).filter(
                ReconciliationMatch.crypto_transaction_id == t.id
            ).first()

            # Check associated entity
            entity_from = db.query(Entity).filter(
                func.lower(Entity.wallet_address) == func.lower(t.wallet_from)
            ).first()
            entity_to = db.query(Entity).filter(
                func.lower(Entity.wallet_address) == func.lower(t.wallet_to)
            ).first()

            # Associated Invoice
            inv = None
            if t.associated_invoice_id:
                inv = db.query(Invoice).filter(Invoice.invoice_number == t.associated_invoice_id).first()
            elif match and match.invoice_id:
                inv = db.query(Invoice).filter(Invoice.id == match.invoice_id).first()

            results.append({
                "id": t.id,
                "transaction_hash": t.transaction_hash,
                "blockchain_network": t.blockchain_network,
                "wallet_from": t.wallet_from,
                "wallet_to": t.wallet_to,
                "from_entity_name": entity_from.name if entity_from else None,
                "to_entity_name": entity_to.name if entity_to else None,
                "asset": t.asset,
                "token_amount": float(t.token_amount),
                "fiat_value": float(t.fiat_value) if t.fiat_value is not None else float(t.token_amount),
                "fiat_currency": t.fiat_currency,
                "gas_fee": float(t.gas_fee) if t.gas_fee is not None else 0.0,
                "gas_fee_fiat": float(t.gas_fee_fiat) if t.gas_fee_fiat is not None else 0.0,
                "confirmation_status": t.confirmation_status,
                "block_number": t.block_number,
                "timestamp": t.transaction_timestamp.isoformat(),
                "associated_invoice_id": t.associated_invoice_id or (inv.invoice_number if inv else None),
                "reconciliation_status": match.match_status if match else ("RECONCILED" if t.associated_invoice_id else "UNMATCHED"),
                "confidence_score": match.confidence_score if match else (95.0 if t.associated_invoice_id else None),
                "explorer_urls": {
                    "tx": tx_url,
                    "from": from_url,
                    "to": to_url,
                },
            })

        return results

    @classmethod
    def get_treasury_wallets(cls, db: Session) -> List[Dict[str, Any]]:
        # Find all corporate entities with wallet addresses
        entities = db.query(Entity).filter(Entity.wallet_address.isnot(None)).all()
        entity_map = {e.wallet_address.lower(): e for e in entities if e.wallet_address}

        # Aggregate wallet balances across CryptoTransaction
        txns = db.query(CryptoTransaction).all()
        wallets_dict: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "network": "ETHEREUM",
            "token_balances": defaultdict(float),
            "total_fiat_value": 0.0,
            "transaction_count": 0,
            "last_activity": None,
        })

        for t in txns:
            # incoming to wallet_to
            w_to = t.wallet_to.lower()
            wallets_dict[w_to]["network"] = t.blockchain_network
            wallets_dict[w_to]["token_balances"][t.asset] += float(t.token_amount)
            val = float(t.fiat_value) if t.fiat_value is not None else float(t.token_amount)
            wallets_dict[w_to]["total_fiat_value"] += val
            wallets_dict[w_to]["transaction_count"] += 1

            # outgoing from wallet_from
            w_from = t.wallet_from.lower()
            wallets_dict[w_from]["network"] = t.blockchain_network
            wallets_dict[w_from]["token_balances"][t.asset] -= float(t.token_amount)
            wallets_dict[w_from]["transaction_count"] += 1

        results = []
        for raw_addr, data in wallets_dict.items():
            matched_entity = entity_map.get(raw_addr)
            explorer_url = BlockExplorerHelper.get_address_url(data["network"], raw_addr)

            # Ensure balances are positive for display
            clean_balances = {k: max(0.0, round(v, 4)) for k, v in data["token_balances"].items()}

            summary = WalletTreasurySummary(
                wallet_address=raw_addr,
                network=data["network"],
                entity_id=matched_entity.id if matched_entity else None,
                entity_name=matched_entity.name if matched_entity else "External / Treasury",
                total_fiat_value=max(0.0, data["total_fiat_value"]),
                token_balances=clean_balances,
                transaction_count=data["transaction_count"],
                explorer_url=explorer_url,
            )
            results.append(summary.to_dict())

        results.sort(key=lambda w: w["total_fiat_value"], reverse=True)
        return results

    @classmethod
    def get_network_analytics(cls, db: Session) -> Dict[str, Any]:
        txns = db.query(CryptoTransaction).all()

        networks = defaultdict(lambda: {
            "total_transactions": 0,
            "total_fiat_volume": 0.0,
            "total_gas_fee_usd": 0.0,
            "assets": defaultdict(float),
        })

        total_volume = 0.0
        total_gas = 0.0

        for t in txns:
            net = t.blockchain_network
            fiat_val = float(t.fiat_value) if t.fiat_value is not None else float(t.token_amount)
            gas_fiat = float(t.gas_fee_fiat) if t.gas_fee_fiat is not None else 0.0

            networks[net]["total_transactions"] += 1
            networks[net]["total_fiat_volume"] += fiat_val
            networks[net]["total_gas_fee_usd"] += gas_fiat
            networks[net]["assets"][t.asset] += float(t.token_amount)

            total_volume += fiat_val
            total_gas += gas_fiat

        # Calculate crypto reconciliation rate
        matched_crypto = db.query(func.count(ReconciliationMatch.id)).filter(
            ReconciliationMatch.crypto_transaction_id.isnot(None)
        ).scalar() or 0

        crypto_match_rate = (matched_crypto / max(1, len(txns))) * 100.0 if txns else 100.0

        return {
            "total_crypto_transactions": len(txns),
            "total_fiat_volume_usd": round(total_volume, 2),
            "total_gas_fee_usd": round(total_gas, 2),
            "crypto_reconciliation_rate": round(crypto_match_rate, 2),
            "networks": {
                net: {
                    "total_transactions": data["total_transactions"],
                    "total_fiat_volume": round(data["total_fiat_volume"], 2),
                    "total_gas_fee_usd": round(data["total_gas_fee_usd"], 2),
                    "assets": {k: round(v, 2) for k, v in data["assets"].items()},
                }
                for net, data in networks.items()
            },
        }
