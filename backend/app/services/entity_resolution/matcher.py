import re
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz
from app.services.normalization.normalizer import NormalizationEngine
from app.services.entity_resolution.models import (
    ConfidenceBucket,
    EntityEvidence,
    EntityMatchCandidate,
    EntityResolutionQuery,
)


class EntityMatcher:
    """
    Deterministic & Explainable Multi-Attribute Entity Matcher.
    Uses strict identifier matching (Wallet, Tax ID, Email, Phone) and
    fuzzy string similarity via RapidFuzz for names and legal entities.
    """

    HIGH_THRESHOLD = 0.85
    MEDIUM_THRESHOLD = 0.65

    @classmethod
    def clean_digits(cls, val: Optional[str]) -> str:
        if not val:
            return ""
        return re.sub(r"\D", "", str(val))

    @classmethod
    def clean_email(cls, val: Optional[str]) -> str:
        if not val:
            return ""
        return str(val).strip().lower()

    @classmethod
    def extract_email_domain(cls, email: Optional[str]) -> Optional[str]:
        if not email or "@" not in email:
            return None
        parts = email.split("@")
        domain = parts[-1].lower().strip()
        # Strip common generic domains
        generic_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com"}
        if domain in generic_domains:
            return None
        # Return domain without TLD (e.g., "acme" from "acme.com")
        domain_name = domain.split(".")[0]
        return domain_name if len(domain_name) >= 3 else None

    @classmethod
    def evaluate_match(
        cls,
        query: EntityResolutionQuery,
        target_entity: Dict[str, Any],
    ) -> Optional[EntityMatchCandidate]:
        """
        Evaluates a single candidate target entity against a resolution query.
        Returns an EntityMatchCandidate with full explainable evidence trail.
        """
        evidence_list: List[EntityEvidence] = []
        matched_identifiers: Dict[str, Any] = {}
        highest_score = 0.0

        target_id = str(target_entity.get("id", ""))
        target_name = str(target_entity.get("name", ""))
        target_legal_name = target_entity.get("legal_name")
        target_tax_id = target_entity.get("tax_id")
        target_email = target_entity.get("email")
        target_phone = target_entity.get("phone")
        target_wallet = target_entity.get("wallet_address")
        target_bank = target_entity.get("bank_account_number")
        target_type = target_entity.get("entity_type", "CUSTOMER")

        # -------------------------------------------------------------
        # 1. Exact Identifier Matches (Highest Deterministic Priority)
        # -------------------------------------------------------------

        # A. Wallet Address (Normalized EVM / Crypto address)
        if query.wallet_address and target_wallet:
            norm_query_wallet = NormalizationEngine.normalize_wallet_address(query.wallet_address).normalized_value
            norm_target_wallet = NormalizationEngine.normalize_wallet_address(target_wallet).normalized_value

            if norm_query_wallet and norm_target_wallet and norm_query_wallet.lower() == norm_target_wallet.lower():
                score = 1.0
                evidence_list.append(
                    EntityEvidence(
                        rule_name="EXACT_WALLET_MATCH",
                        score_contribution=score,
                        algorithm="exact_case_insensitive",
                        query_value=query.wallet_address,
                        target_value=target_wallet,
                        explanation=f"Exact on-chain wallet address match ({norm_query_wallet})",
                    )
                )
                matched_identifiers["wallet_address"] = True
                highest_score = max(highest_score, score)

        # B. Tax ID / EIN / VAT
        if query.tax_id and target_tax_id:
            clean_q_tax = cls.clean_digits(query.tax_id)
            clean_t_tax = cls.clean_digits(target_tax_id)
            if clean_q_tax and clean_t_tax and clean_q_tax == clean_t_tax:
                score = 1.0
                evidence_list.append(
                    EntityEvidence(
                        rule_name="EXACT_TAX_ID_MATCH",
                        score_contribution=score,
                        algorithm="exact_digits_match",
                        query_value=query.tax_id,
                        target_value=target_tax_id,
                        explanation=f"Exact normalized tax ID match ({clean_q_tax})",
                    )
                )
                matched_identifiers["tax_id"] = True
                highest_score = max(highest_score, score)

        # C. Email Address
        if query.email and target_email:
            clean_q_email = cls.clean_email(query.email)
            clean_t_email = cls.clean_email(target_email)
            if clean_q_email == clean_t_email:
                score = 0.95
                evidence_list.append(
                    EntityEvidence(
                        rule_name="EXACT_EMAIL_MATCH",
                        score_contribution=score,
                        algorithm="exact_email_lowercase",
                        query_value=query.email,
                        target_value=target_email,
                        explanation=f"Exact email identity match ({clean_q_email})",
                    )
                )
                matched_identifiers["email"] = True
                highest_score = max(highest_score, score)

        # D. Phone Number
        if query.phone and target_phone:
            clean_q_phone = cls.clean_digits(query.phone)
            clean_t_phone = cls.clean_digits(target_phone)
            if clean_q_phone and clean_t_phone and (clean_q_phone.endswith(clean_t_phone[-10:]) or clean_t_phone.endswith(clean_q_phone[-10:])):
                score = 0.90
                evidence_list.append(
                    EntityEvidence(
                        rule_name="EXACT_PHONE_MATCH",
                        score_contribution=score,
                        algorithm="last_10_digits_match",
                        query_value=query.phone,
                        target_value=target_phone,
                        explanation=f"Exact phone number match on last 10 digits ({clean_q_phone[-10:]})",
                    )
                )
                matched_identifiers["phone"] = True
                highest_score = max(highest_score, score)

        # E. Bank Account Number
        if query.bank_account_number and target_bank:
            clean_q_bank = cls.clean_digits(query.bank_account_number)
            clean_t_bank = cls.clean_digits(target_bank)
            if clean_q_bank and clean_t_bank and clean_q_bank == clean_t_bank:
                score = 0.95
                evidence_list.append(
                    EntityEvidence(
                        rule_name="EXACT_BANK_ACCOUNT_MATCH",
                        score_contribution=score,
                        algorithm="exact_account_digits",
                        query_value=query.bank_account_number,
                        target_value=target_bank,
                        explanation="Exact bank account digits match",
                    )
                )
                matched_identifiers["bank_account"] = True
                highest_score = max(highest_score, score)

        # -------------------------------------------------------------
        # 2. Fuzzy Name & Legal Entity Matching via RapidFuzz
        # -------------------------------------------------------------
        if query.name and (target_name or target_legal_name):
            norm_q_name = NormalizationEngine.normalize_company_name(query.name).normalized_value or query.name.strip().lower()
            
            candidates_to_compare = []
            if target_name:
                candidates_to_compare.append(("name", target_name))
            if target_legal_name:
                candidates_to_compare.append(("legal_name", target_legal_name))

            best_name_sim = 0.0
            best_algo = ""
            best_target_val = ""
            best_field = ""

            for field_type, raw_target in candidates_to_compare:
                norm_t = NormalizationEngine.normalize_company_name(raw_target).normalized_value or raw_target.strip().lower()

                # Test 1: Token sort ratio (handles token rearrangements)
                ts_ratio = fuzz.token_sort_ratio(norm_q_name, norm_t) / 100.0
                # Test 2: Token set ratio (handles subset words, e.g. "Acme Corp" in "Acme Corporation LLC")
                tset_ratio = fuzz.token_set_ratio(norm_q_name, norm_t) / 100.0
                # Test 3: Raw ratio
                r_ratio = fuzz.ratio(norm_q_name, norm_t) / 100.0

                effective_sim = max(ts_ratio, tset_ratio * 0.95, r_ratio)

                if effective_sim > best_name_sim:
                    best_name_sim = effective_sim
                    best_algo = "token_sort_ratio" if ts_ratio >= tset_ratio else "token_set_ratio"
                    best_target_val = raw_target
                    best_field = field_type

            if best_name_sim >= 0.60:
                name_score = round(best_name_sim, 4)
                evidence_list.append(
                    EntityEvidence(
                        rule_name=f"FUZZY_{best_field.upper()}_MATCH",
                        score_contribution=name_score,
                        algorithm=best_algo,
                        query_value=query.name,
                        target_value=best_target_val,
                        explanation=f"RapidFuzz {best_algo} yielded {int(best_name_sim * 100)}% similarity between '{norm_q_name}' and '{best_target_val}'",
                    )
                )
                matched_identifiers[best_field] = name_score
                highest_score = max(highest_score, name_score)

        # -------------------------------------------------------------
        # 3. Domain & Contextual Corroboration
        # -------------------------------------------------------------
        if query.email and target_name and highest_score < 0.90:
            domain = cls.extract_email_domain(query.email)
            if domain and domain in target_name.lower():
                domain_boost = 0.10
                new_score = min(0.85, highest_score + domain_boost)
                evidence_list.append(
                    EntityEvidence(
                        rule_name="DOMAIN_NAME_CORRELATION",
                        score_contribution=domain_boost,
                        algorithm="domain_keyword_search",
                        query_value=query.email,
                        target_value=target_name,
                        explanation=f"Query email domain '{domain}' matches entity brand '{target_name}'",
                    )
                )
                matched_identifiers["domain_correlation"] = True
                highest_score = new_score

        # Only return candidate if there is sufficient similarity or match evidence
        if highest_score < 0.40 or not evidence_list:
            return None

        # Assign confidence bucket
        if highest_score >= cls.HIGH_THRESHOLD:
            bucket = ConfidenceBucket.HIGH
        elif highest_score >= cls.MEDIUM_THRESHOLD:
            bucket = ConfidenceBucket.MEDIUM
        else:
            bucket = ConfidenceBucket.LOW

        return EntityMatchCandidate(
            entity_id=target_id,
            name=target_name,
            legal_name=target_legal_name,
            entity_type=target_type,
            tax_id=target_tax_id,
            email=target_email,
            phone=target_phone,
            wallet_address=target_wallet,
            bank_account_number=target_bank,
            confidence_score=highest_score,
            confidence_bucket=bucket,
            matched_identifiers=matched_identifiers,
            evidence=evidence_list,
        )
