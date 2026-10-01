from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfidenceBucket(str, Enum):
    HIGH = "HIGH"        # Score >= 0.85 or exact strong identifier
    MEDIUM = "MEDIUM"    # 0.65 <= Score < 0.85
    LOW = "LOW"          # Score < 0.65


class EntityEvidence(BaseModel):
    rule_name: str
    score_contribution: float
    algorithm: Optional[str] = None
    query_value: Optional[str] = None
    target_value: Optional[str] = None
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "score_contribution": round(self.score_contribution, 4),
            "algorithm": self.algorithm,
            "query_value": self.query_value,
            "target_value": self.target_value,
            "explanation": self.explanation,
        }


class EntityMatchCandidate(BaseModel):
    entity_id: str
    name: str
    legal_name: Optional[str] = None
    entity_type: str = "CUSTOMER"
    tax_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    wallet_address: Optional[str] = None
    bank_account_number: Optional[str] = None
    confidence_score: float
    confidence_bucket: ConfidenceBucket
    matched_identifiers: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[EntityEvidence] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "legal_name": self.legal_name,
            "entity_type": self.entity_type,
            "tax_id": self.tax_id,
            "email": self.email,
            "phone": self.phone,
            "wallet_address": self.wallet_address,
            "bank_account_number": self.bank_account_number,
            "confidence_score": round(self.confidence_score, 4),
            "confidence_bucket": self.confidence_bucket.value,
            "matched_identifiers": self.matched_identifiers,
            "evidence": [e.to_dict() for e in self.evidence],
        }


class EntityResolutionQuery(BaseModel):
    name: Optional[str] = Field(None, description="Counterparty, customer or vendor name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    tax_id: Optional[str] = Field(None, description="Tax ID, EIN, VAT, GST")
    wallet_address: Optional[str] = Field(None, description="EVM or other crypto wallet address")
    bank_account_number: Optional[str] = Field(None, description="Bank account or IBAN")
    reference_id: Optional[str] = Field(None, description="Source transaction or record reference")


class EntityResolutionResult(BaseModel):
    query: EntityResolutionQuery
    resolved: bool = False
    best_match: Optional[EntityMatchCandidate] = None
    candidates: List[EntityMatchCandidate] = Field(default_factory=list)
    requires_manual_review: bool = False
    resolution_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query.model_dump(),
            "resolved": self.resolved,
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "candidates": [c.to_dict() for c in self.candidates],
            "requires_manual_review": self.requires_manual_review,
            "resolution_notes": self.resolution_notes,
        }
