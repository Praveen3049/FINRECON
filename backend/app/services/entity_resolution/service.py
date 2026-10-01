from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.entity import Entity
from app.models.transaction import Transaction
from app.models.invoice import Invoice
from app.services.entity_resolution.models import (
    ConfidenceBucket,
    EntityMatchCandidate,
    EntityResolutionQuery,
    EntityResolutionResult,
)
from app.services.entity_resolution.matcher import EntityMatcher


class EntityResolutionService:
    """
    Coordinates multi-source entity resolution, database entity lookups,
    ambiguity detection, and transaction linking.
    """

    @classmethod
    def entity_to_dict(cls, entity: Entity) -> Dict[str, Any]:
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
        }

    @classmethod
    def resolve_query(
        cls,
        query: EntityResolutionQuery,
        db: Optional[Session] = None,
        candidate_entities: Optional[List[Dict[str, Any]]] = None,
    ) -> EntityResolutionResult:
        """
        Resolves an EntityResolutionQuery against known entities (either from DB or provided list).
        """
        pool: List[Dict[str, Any]] = []

        if candidate_entities is not None:
            pool = candidate_entities
        elif db is not None:
            db_entities = db.query(Entity).all()
            pool = [cls.entity_to_dict(e) for e in db_entities]

        if not pool:
            return EntityResolutionResult(
                query=query,
                resolved=False,
                best_match=None,
                candidates=[],
                requires_manual_review=False,
                resolution_notes="No target entities available to compare against.",
            )

        evaluated_candidates: List[EntityMatchCandidate] = []
        for candidate in pool:
            match_res = EntityMatcher.evaluate_match(query, candidate)
            if match_res is not None:
                evaluated_candidates.append(match_res)

        # Sort candidates descending by confidence score
        evaluated_candidates.sort(key=lambda c: c.confidence_score, reverse=True)

        if not evaluated_candidates:
            return EntityResolutionResult(
                query=query,
                resolved=False,
                best_match=None,
                candidates=[],
                requires_manual_review=False,
                resolution_notes="No matching entity candidates met the minimum similarity threshold.",
            )

        best = evaluated_candidates[0]

        # Check for Ambiguity: If second candidate is within 5% score of best and score >= 0.70
        is_ambiguous = False
        if len(evaluated_candidates) > 1:
            second = evaluated_candidates[1]
            if (best.confidence_score - second.confidence_score) < 0.05 and second.confidence_score >= 0.70:
                is_ambiguous = True

        if is_ambiguous:
            second = evaluated_candidates[1]
            return EntityResolutionResult(
                query=query,
                resolved=False,
                best_match=best,
                candidates=evaluated_candidates,
                requires_manual_review=True,
                resolution_notes=(
                    f"Ambiguous match detected between '{best.name}' ({int(best.confidence_score * 100)}%) "
                    f"and '{second.name}' ({int(second.confidence_score * 100)}%). Manual review required."
                ),
            )

        if best.confidence_bucket == ConfidenceBucket.HIGH:
            return EntityResolutionResult(
                query=query,
                resolved=True,
                best_match=best,
                candidates=evaluated_candidates,
                requires_manual_review=False,
                resolution_notes=f"Resolved with HIGH confidence ({int(best.confidence_score * 100)}%) to '{best.name}'.",
            )

        elif best.confidence_bucket == ConfidenceBucket.MEDIUM:
            return EntityResolutionResult(
                query=query,
                resolved=False,
                best_match=best,
                candidates=evaluated_candidates,
                requires_manual_review=True,
                resolution_notes=(
                    f"Potential match with MEDIUM confidence ({int(best.confidence_score * 100)}%) to '{best.name}'. "
                    "Manual verification recommended."
                ),
            )

        else:
            return EntityResolutionResult(
                query=query,
                resolved=False,
                best_match=best,
                candidates=evaluated_candidates,
                requires_manual_review=False,
                resolution_notes="Only LOW confidence candidates identified. Recommend registering a new entity.",
            )

    @classmethod
    def get_all_entities_summary(cls, db: Session, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        entities = db.query(Entity).offset(offset).limit(limit).all()
        results = []

        for e in entities:
            txn_count = db.query(func.count(Transaction.id)).filter(Transaction.entity_id == e.id).scalar() or 0
            inv_count = db.query(func.count(Invoice.id)).filter(Invoice.entity_id == e.id).scalar() or 0

            results.append({
                "id": e.id,
                "name": e.name,
                "legal_name": e.legal_name,
                "entity_type": e.entity_type,
                "tax_id": e.tax_id,
                "email": e.email,
                "phone": e.phone,
                "wallet_address": e.wallet_address,
                "bank_account_number": e.bank_account_number,
                "transaction_count": txn_count,
                "invoice_count": inv_count,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            })
        return results

    @classmethod
    def link_transaction(cls, db: Session, transaction_id: str, entity_id: str) -> Optional[Transaction]:
        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not txn or not entity:
            return None
        txn.entity_id = entity.id
        db.commit()
        db.refresh(txn)
        return txn
