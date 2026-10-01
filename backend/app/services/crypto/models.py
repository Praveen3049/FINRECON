from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BlockchainNetwork(str, Enum):
    ETHEREUM = "ETHEREUM"
    POLYGON = "POLYGON"
    ARBITRUM = "ARBITRUM"
    SOLANA = "SOLANA"
    BITCOIN = "BITCOIN"


class CryptoAssetType(str, Enum):
    NATIVE = "NATIVE"
    ERC20_STABLECOIN = "ERC20_STABLECOIN"
    ERC20_TOKEN = "ERC20_TOKEN"


class BlockExplorerHelper:
    EXPLORER_BASE_URLS = {
        "ETHEREUM": {"tx": "https://etherscan.io/tx/", "address": "https://etherscan.io/address/"},
        "POLYGON": {"tx": "https://polygonscan.com/tx/", "address": "https://polygonscan.com/address/"},
        "ARBITRUM": {"tx": "https://arbiscan.io/tx/", "address": "https://arbiscan.io/address/"},
        "SOLANA": {"tx": "https://solscan.io/tx/", "address": "https://solscan.io/account/"},
        "BITCOIN": {"tx": "https://mempool.space/tx/", "address": "https://mempool.space/address/"},
    }

    @classmethod
    def get_tx_url(cls, network: str, tx_hash: str) -> str:
        net = network.upper().strip()
        base = cls.EXPLORER_BASE_URLS.get(net, cls.EXPLORER_BASE_URLS["ETHEREUM"])["tx"]
        return f"{base}{tx_hash}"

    @classmethod
    def get_address_url(cls, network: str, address: str) -> str:
        net = network.upper().strip()
        base = cls.EXPLORER_BASE_URLS.get(net, cls.EXPLORER_BASE_URLS["ETHEREUM"])["address"]
        return f"{base}{address}"


class GasFeeCalculation(BaseModel):
    network: str
    native_token: str
    gas_units: int
    gas_price_gwei: float
    gas_fee_native: float
    native_usd_price: float
    gas_fee_usd: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "network": self.network,
            "native_token": self.native_token,
            "gas_units": self.gas_units,
            "gas_price_gwei": round(self.gas_price_gwei, 2),
            "gas_fee_native": round(self.gas_fee_native, 6),
            "native_usd_price": round(self.native_usd_price, 2),
            "gas_fee_usd": round(self.gas_fee_usd, 4),
        }


class SlippageAnalysis(BaseModel):
    expected_fiat_amount: float
    actual_fiat_amount: float
    slippage_usd: float
    slippage_percentage: float
    tolerance_percentage: float = 0.5
    is_acceptable: bool
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expected_fiat_amount": round(self.expected_fiat_amount, 2),
            "actual_fiat_amount": round(self.actual_fiat_amount, 2),
            "slippage_usd": round(self.slippage_usd, 2),
            "slippage_percentage": round(self.slippage_percentage, 2),
            "tolerance_percentage": self.tolerance_percentage,
            "is_acceptable": self.is_acceptable,
            "notes": self.notes,
        }


class WalletTreasurySummary(BaseModel):
    wallet_address: str
    network: str
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    total_fiat_value: float = 0.0
    token_balances: Dict[str, float] = Field(default_factory=dict)
    transaction_count: int = 0
    explorer_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_address": self.wallet_address,
            "network": self.network,
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "total_fiat_value": round(self.total_fiat_value, 2),
            "token_balances": {k: round(v, 4) for k, v in self.token_balances.items()},
            "transaction_count": self.transaction_count,
            "explorer_url": self.explorer_url,
        }
