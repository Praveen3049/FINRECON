from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from rapidfuzz import fuzz

from app.services.normalization.normalizer import NormalizationEngine
from app.services.reconciliation.models import (
    ConfidenceLevel,
    DiscrepancyDetail,
    DiscrepancyType,
    MatchAlgorithmPass,
    MatchCandidateResult,
    MatchEvidence,
    MatchStatus,
)


class ReconciliationEngine:
    """
    Deterministic Multi-Pass Financial Reconciliation Engine.
    Executes sequential passes (Exact, ID Correlation, Fee Netting, Crypto,
    Fuzzy Entity, Duplicate Detection, and Orphan Exceptions).
    """

    @classmethod
    def get_txn_ext_id(cls, t: Any) -> str:
        return str(getattr(t, "external_transaction_id", None) or getattr(t, "transaction_id", None) or getattr(t, "id", "TXN"))

    @classmethod
    def get_txn_counterparty(cls, t: Any) -> str:
        return str(getattr(t, "counterparty_normalized_name", None) or getattr(t, "counterparty_raw_name", None) or getattr(t, "counterparty_name", "") or "")

    @classmethod
    def get_txn_ref(cls, t: Any) -> str:
        return str(
            getattr(t, "payment_reference", None)
            or getattr(t, "reference_number", None)
            or getattr(t, "external_transaction_id", None)
            or ""
        ).strip().upper()

    @classmethod
    def run_multi_pass_reconciliation(
        cls,
        transactions: List[Any],
        invoices: List[Any],
        crypto_transactions: List[Any],
        date_tolerance_days: int = 3,
        amount_tolerance: float = 0.05,
    ) -> List[MatchCandidateResult]:
        """
        Executes all 7 reconciliation passes deterministically.
        Returns a list of MatchCandidateResult containing matches, confidence, evidence, and discrepancies.
        """
        results: List[MatchCandidateResult] = []
        matched_txn_ids: Set[str] = set()
        matched_inv_ids: Set[str] = set()
        matched_crypto_ids: Set[str] = set()

        # Separate transactions by source type
        bank_txns = [t for t in transactions if getattr(t, "source_type", "") == "BANK"]
        gateway_txns = [t for t in transactions if getattr(t, "source_type", "") == "PAYMENT_GATEWAY"]
        erp_txns = [t for t in transactions if getattr(t, "source_type", "") == "ACCOUNTING"]

        # -------------------------------------------------------------
        # PASS 1: Exact Match (Exact ID, Date, Amount, Currency)
        # -------------------------------------------------------------
        # 1A: Bank <-> Gateway exact match
        for b in bank_txns:
            if b.id in matched_txn_ids:
                continue
            for g in gateway_txns:
                if g.id in matched_txn_ids:
                    continue

                b_ref = cls.get_txn_ref(b)
                g_ref = cls.get_txn_ref(g)
                ref_match = bool(b_ref and g_ref and b_ref == g_ref)
                amt_match = abs(float(b.amount) - float(g.amount)) <= amount_tolerance
                date_match = b.transaction_date == g.transaction_date
                curr_match = b.currency == g.currency

                if ref_match and amt_match and date_match and curr_match:
                    matched_txn_ids.add(b.id)
                    matched_txn_ids.add(g.id)

                    b_ext = cls.get_txn_ext_id(b)
                    g_ext = cls.get_txn_ext_id(g)
                    evidence = [
                        MatchEvidence(
                            rule_name="EXACT_TRANSACTION_MATCH",
                            algorithm_pass=MatchAlgorithmPass.PASS_1_EXACT,
                            score_contribution=100.0,
                            explanation=(
                                f"Exact match between Bank '{b_ext}' and Gateway '{g_ext}' "
                                f"on amount ({b.currency} {b.amount}) and reference '{b.payment_reference}'."
                            ),
                            details={"amount": float(b.amount), "reference": b.payment_reference},
                        )
                    ]
                    results.append(
                        MatchCandidateResult(
                            match_type="TXN_TO_TXN",
                            match_status=MatchStatus.EXACT_MATCH,
                            confidence_score=100.0,
                            confidence_level=ConfidenceLevel.HIGH,
                            algorithm_pass=MatchAlgorithmPass.PASS_1_EXACT,
                            source_transaction_id=b.id,
                            matched_transaction_id=g.id,
                            evidence=evidence,
                            discrepancies=[],
                        )
                    )
                    break

        # 1B: Gateway/Bank <-> Invoice exact match
        for t in transactions:
            if t.id in matched_txn_ids:
                continue
            for inv in invoices:
                if inv.id in matched_inv_ids:
                    continue

                t_ord = str(getattr(t, "reference_order_id", "") or "").strip().upper()
                inv_ord = str(getattr(inv, "reference_order_id", "") or "").strip().upper()
                order_match = bool(t_ord and inv_ord and t_ord == inv_ord)

                t_ref = cls.get_txn_ref(t)
                inv_num = str(getattr(inv, "invoice_number", "") or "").strip().upper()
                t_desc = str(getattr(t, "description", "") or "").strip().upper()
                inv_no_match = bool(inv_num and (inv_num in t_ref or inv_num in t_desc))

                t_inv_ref = str(getattr(t, "invoice_reference", "") or "").strip()
                inv_ref_match = bool(t_inv_ref and (t_inv_ref == str(inv.id) or t_inv_ref.upper() == inv_num))

                amt_match = abs(float(t.amount) - float(inv.total_amount)) <= amount_tolerance
                curr_match = t.currency == inv.currency

                if (order_match or inv_no_match or inv_ref_match) and amt_match and curr_match:
                    matched_txn_ids.add(t.id)
                    matched_inv_ids.add(inv.id)

                    t_ext = cls.get_txn_ext_id(t)
                    evidence = [
                        MatchEvidence(
                            rule_name="EXACT_INVOICE_ORDER_MATCH",
                            algorithm_pass=MatchAlgorithmPass.PASS_1_EXACT,
                            score_contribution=100.0,
                            explanation=(
                                f"Transaction '{t_ext}' exactly matches Invoice '{inv.invoice_number}' "
                                f"for amount {t.currency} {t.amount}."
                            ),
                            details={"invoice_number": inv.invoice_number, "order_id": inv.reference_order_id},
                        )
                    ]
                    results.append(
                        MatchCandidateResult(
                            match_type="TXN_TO_INVOICE",
                            match_status=MatchStatus.EXACT_MATCH,
                            confidence_score=100.0,
                            confidence_level=ConfidenceLevel.HIGH,
                            algorithm_pass=MatchAlgorithmPass.PASS_1_EXACT,
                            source_transaction_id=t.id,
                            invoice_id=inv.id,
                            evidence=evidence,
                            discrepancies=[],
                        )
                    )
                    break

        # -------------------------------------------------------------
        # PASS 2: ID Correlation with Settlement Date Lag (T±3)
        # -------------------------------------------------------------
        for b in bank_txns:
            if b.id in matched_txn_ids:
                continue
            for g in gateway_txns:
                if g.id in matched_txn_ids:
                    continue

                b_ref = cls.get_txn_ref(b)
                g_ref = cls.get_txn_ref(g)
                ref_match = bool(b_ref and g_ref and b_ref == g_ref)
                amt_match = abs(float(b.amount) - float(g.amount)) <= amount_tolerance
                curr_match = b.currency == g.currency

                if ref_match and amt_match and curr_match and b.transaction_date and g.transaction_date:
                    days_diff = abs((b.transaction_date - g.transaction_date).days)
                    if 0 < days_diff <= date_tolerance_days:
                        matched_txn_ids.add(b.id)
                        matched_txn_ids.add(g.id)

                        discrepancies = [
                            DiscrepancyDetail(
                                discrepancy_type=DiscrepancyType.DATE,
                                field_name="transaction_date",
                                source_value=str(b.transaction_date),
                                matched_value=str(g.transaction_date),
                                difference_numeric=float(days_diff),
                                root_cause_category="T_PLUS_LAG",
                                severity="LOW",
                            )
                        ]
                        evidence = [
                            MatchEvidence(
                                rule_name="SETTLEMENT_DATE_LAG_MATCH",
                                algorithm_pass=MatchAlgorithmPass.PASS_2_ID_CORRELATION,
                                score_contribution=95.0,
                                explanation=(
                                    f"Reference '{b.payment_reference}' matches exactly with T+{days_diff} "
                                    f"settlement timing lag between Gateway and Bank."
                                ),
                                details={"lag_days": days_diff},
                            )
                        ]
                        results.append(
                            MatchCandidateResult(
                                match_type="TXN_TO_TXN",
                                match_status=MatchStatus.PARTIAL_MATCH,
                                confidence_score=95.0,
                                confidence_level=ConfidenceLevel.HIGH,
                                algorithm_pass=MatchAlgorithmPass.PASS_2_ID_CORRELATION,
                                source_transaction_id=b.id,
                                matched_transaction_id=g.id,
                                evidence=evidence,
                                discrepancies=discrepancies,
                            )
                        )
                        break

        # -------------------------------------------------------------
        # PASS 3: Gateway Processing Fee Deduction & Netting
        # -------------------------------------------------------------
        for b in bank_txns:
            if b.id in matched_txn_ids:
                continue
            for g in gateway_txns:
                if g.id in matched_txn_ids:
                    continue

                fee = float(getattr(g, "fee_amount", 0) or 0)
                gross_amt = float(g.amount)
                expected_net = gross_amt - fee
                bank_amt = float(b.amount)

                # Check if Bank deposited net amount (gross - fee) and identical currency
                diff = abs(bank_amt - expected_net)
                curr_match = b.currency == g.currency

                if diff <= amount_tolerance and fee > 0 and curr_match:
                    days_diff = 0
                    if b.transaction_date and g.transaction_date:
                        days_diff = abs((b.transaction_date - g.transaction_date).days)

                    if days_diff <= date_tolerance_days:
                        # Corroborate reference or counterparty if available
                        b_ref = cls.get_txn_ref(b)
                        g_ref = cls.get_txn_ref(g)
                        b_name = cls.get_txn_counterparty(b)
                        g_name = cls.get_txn_counterparty(g)

                        ref_compatible = (
                            not b_ref
                            or not g_ref
                            or (b_ref == g_ref or b_ref in g_ref or g_ref in b_ref)
                        )
                        name_sim = (
                            fuzz.token_sort_ratio(b_name.lower(), g_name.lower()) / 100.0
                            if (b_name and g_name)
                            else 1.0
                        )

                        if not (ref_compatible or name_sim >= 0.60):
                            continue

                        matched_txn_ids.add(b.id)
                        matched_txn_ids.add(g.id)

                        discrepancies = [
                            DiscrepancyDetail(
                                discrepancy_type=DiscrepancyType.AMOUNT,
                                field_name="amount",
                                source_value=f"{b.currency} {bank_amt:.2f}",
                                matched_value=f"{g.currency} {gross_amt:.2f}",
                                difference_numeric=float(fee),
                                difference_percentage=round((fee / gross_amt) * 100, 2),
                                root_cause_category="PROCESSING_FEE",
                                severity="MEDIUM",
                            )
                        ]
                        if days_diff > 0:
                            discrepancies.append(
                                DiscrepancyDetail(
                                    discrepancy_type=DiscrepancyType.DATE,
                                    field_name="transaction_date",
                                    source_value=str(b.transaction_date),
                                    matched_value=str(g.transaction_date),
                                    difference_numeric=float(days_diff),
                                    root_cause_category="T_PLUS_LAG",
                                    severity="LOW",
                                )
                            )

                        evidence = [
                            MatchEvidence(
                                rule_name="GATEWAY_PROCESSING_FEE_NETTING",
                                algorithm_pass=MatchAlgorithmPass.PASS_3_FEE_NETTING,
                                score_contribution=92.0,
                                explanation=(
                                    f"Bank deposit {b.currency} {bank_amt:.2f} matches Gateway gross {gross_amt:.2f} "
                                    f"less detected processing fee of {fee:.2f}."
                                ),
                                details={"gross": gross_amt, "fee": fee, "net": bank_amt},
                            )
                        ]
                        results.append(
                            MatchCandidateResult(
                                match_type="TXN_TO_TXN",
                                match_status=MatchStatus.PARTIAL_MATCH,
                                confidence_score=92.0,
                                confidence_level=ConfidenceLevel.HIGH,
                                algorithm_pass=MatchAlgorithmPass.PASS_3_FEE_NETTING,
                                source_transaction_id=b.id,
                                matched_transaction_id=g.id,
                                evidence=evidence,
                                discrepancies=discrepancies,
                            )
                        )
                        break

        # -------------------------------------------------------------
        # PASS 4: Crypto On-Chain Transaction & Hash Match
        # -------------------------------------------------------------
        for c in crypto_transactions:
            if c.id in matched_crypto_ids:
                continue

            tx_hash = getattr(c, "transaction_hash", None) or getattr(c, "tx_hash", "0x0000000000")
            network = getattr(c, "blockchain_network", None) or getattr(c, "blockchain", "ETHEREUM")
            c_memo = str(getattr(c, "associated_reference", None) or getattr(c, "associated_invoice_id", None) or getattr(c, "memo", None) or "")
            c_val = float(getattr(c, "fiat_value", None) or getattr(c, "amount_usd", None) or getattr(c, "token_amount", None) or getattr(c, "amount", 0) or 0)

            # 4A: Crypto <-> Invoice match
            for inv in invoices:
                if inv.id in matched_inv_ids:
                    continue

                inv_num = getattr(inv, "invoice_number", "")
                ref_in_memo = (
                    bool(c_memo)
                    and bool(inv_num)
                    and inv_num.strip().upper() in c_memo.strip().upper()
                )
                inv_amt = float(inv.total_amount)
                val_diff = abs(c_val - inv_amt)

                if (ref_in_memo or val_diff <= amount_tolerance) and val_diff <= 10.0:
                    matched_crypto_ids.add(c.id)
                    matched_inv_ids.add(inv.id)

                    discrepancies = []
                    if val_diff > amount_tolerance:
                        discrepancies.append(
                            DiscrepancyDetail(
                                discrepancy_type=DiscrepancyType.AMOUNT,
                                field_name="amount",
                                source_value=f"USD {c_val:.2f}",
                                matched_value=f"{inv.currency} {inv_amt:.2f}",
                                difference_numeric=float(val_diff),
                                root_cause_category="SLIPPAGE",
                                severity="LOW",
                            )
                        )

                    evidence = [
                        MatchEvidence(
                            rule_name="ON_CHAIN_CRYPTO_INVOICE_MATCH",
                            algorithm_pass=MatchAlgorithmPass.PASS_4_CRYPTO_ON_CHAIN,
                            score_contribution=95.0,
                            explanation=(
                                f"On-chain transaction '{tx_hash[:10]}...{tx_hash[-6:]}' on {network} "
                                f"matches Invoice '{inv_num}'."
                            ),
                            details={"tx_hash": tx_hash, "blockchain": network, "usd_value": c_val},
                        )
                    ]
                    results.append(
                        MatchCandidateResult(
                            match_type="CRYPTO_TO_INVOICE",
                            match_status=MatchStatus.EXACT_MATCH if not discrepancies else MatchStatus.PARTIAL_MATCH,
                            confidence_score=95.0,
                            confidence_level=ConfidenceLevel.HIGH,
                            algorithm_pass=MatchAlgorithmPass.PASS_4_CRYPTO_ON_CHAIN,
                            crypto_transaction_id=c.id,
                            invoice_id=inv.id,
                            evidence=evidence,
                            discrepancies=discrepancies,
                        )
                    )
                    break

            # 4B: Crypto <-> ERP Accounting Transaction match
            if c.id not in matched_crypto_ids:
                for erp in erp_txns:
                    if erp.id in matched_txn_ids:
                        continue

                    ref_match = (
                        erp.payment_reference
                        and (erp.payment_reference.lower() in tx_hash.lower() or tx_hash.lower() in erp.payment_reference.lower())
                    )
                    erp_amt = float(erp.amount)
                    val_diff = abs(c_val - erp_amt)

                    if ref_match or val_diff <= 1.0:
                        matched_crypto_ids.add(c.id)
                        matched_txn_ids.add(erp.id)

                        erp_ext = cls.get_txn_ext_id(erp)
                        evidence = [
                            MatchEvidence(
                                rule_name="CRYPTO_ERP_LEDGER_MATCH",
                                algorithm_pass=MatchAlgorithmPass.PASS_4_CRYPTO_ON_CHAIN,
                                score_contribution=94.0,
                                explanation=(
                                    f"Crypto treasury txn '{tx_hash[:10]}...' matches ERP journal entry '{erp_ext}'."
                                ),
                                details={"tx_hash": tx_hash, "erp_id": erp_ext},
                            )
                        ]
                        results.append(
                            MatchCandidateResult(
                                match_type="CRYPTO_TO_ERP",
                                match_status=MatchStatus.EXACT_MATCH,
                                confidence_score=94.0,
                                confidence_level=ConfidenceLevel.HIGH,
                                algorithm_pass=MatchAlgorithmPass.PASS_4_CRYPTO_ON_CHAIN,
                                crypto_transaction_id=c.id,
                                matched_transaction_id=erp.id,
                                evidence=evidence,
                                discrepancies=[],
                            )
                        )
                        break

        # -------------------------------------------------------------
        # PASS 5: Fuzzy Entity & Windowed Amount Matching
        # -------------------------------------------------------------
        for b in bank_txns:
            if b.id in matched_txn_ids:
                continue
            for g in gateway_txns + erp_txns:
                if g.id in matched_txn_ids:
                    continue

                curr_match = (b.currency == g.currency)
                if not curr_match:
                    continue

                b_name = cls.get_txn_counterparty(b)
                g_name = cls.get_txn_counterparty(g)
                if not b_name or not g_name:
                    continue

                sim = fuzz.token_sort_ratio(b_name.lower(), g_name.lower()) / 100.0
                amt_match = abs(float(b.amount) - float(g.amount)) <= amount_tolerance

                if sim >= 0.85 and amt_match:
                    days_diff = 0
                    if b.transaction_date and g.transaction_date:
                        days_diff = abs((b.transaction_date - g.transaction_date).days)

                    if days_diff <= date_tolerance_days:
                        matched_txn_ids.add(b.id)
                        matched_txn_ids.add(g.id)

                        score = round(sim * 100.0, 1)
                        evidence = [
                            MatchEvidence(
                                rule_name="FUZZY_ENTITY_AMOUNT_MATCH",
                                algorithm_pass=MatchAlgorithmPass.PASS_5_FUZZY_ENTITY_AMOUNT,
                                score_contribution=score,
                                explanation=(
                                    f"Fuzzy counterparty match ({int(score)}%) between '{b_name}' and '{g_name}' "
                                    f"with identical amount {b.currency} {b.amount}."
                                ),
                                details={"similarity": score, "lag_days": days_diff},
                            )
                        ]
                        results.append(
                            MatchCandidateResult(
                                match_type="TXN_TO_TXN",
                                match_status=MatchStatus.PARTIAL_MATCH,
                                confidence_score=score,
                                confidence_level=ConfidenceLevel.HIGH if score >= 85.0 else ConfidenceLevel.MEDIUM,
                                algorithm_pass=MatchAlgorithmPass.PASS_5_FUZZY_ENTITY_AMOUNT,
                                source_transaction_id=b.id,
                                matched_transaction_id=g.id,
                                evidence=evidence,
                                discrepancies=[],
                            )
                        )
                        break

        # -------------------------------------------------------------
        # PASS 6: Duplicate Detection
        # -------------------------------------------------------------
        seen_txns: Dict[str, Any] = {}
        for t in transactions:
            raw_ref = t.payment_reference or getattr(t, "reference_number", None) or getattr(t, "external_transaction_id", None)
            if not raw_ref:
                continue
            ref = str(raw_ref).strip().upper()
            # Only perform duplicate detection if we have a meaningful reference
            if ref.startswith("BTX_"):  # Prevent raw bank lines without refs from false-flagging
                continue
                
            t_dir = getattr(t, "direction", "CREDIT")
            t_date = getattr(t, "transaction_date", None)
            amt_str = f"{float(t.amount):.2f}"
            key = f"{t.source_type}_{t_dir}_{amt_str}_{t.currency}_{t_date}_{ref}"
            if key in seen_txns:
                dup_t = seen_txns[key]
                t_ext = cls.get_txn_ext_id(t)
                dup_ext = cls.get_txn_ext_id(dup_t)
                dup_amt = float(getattr(t, "amount", 0.0))
                discrepancies = [
                    DiscrepancyDetail(
                        discrepancy_type=DiscrepancyType.DUPLICATE_ENTRY,
                        field_name="transaction_id",
                        source_value=t_ext,
                        matched_value=dup_ext,
                        difference_numeric=dup_amt,
                        difference_percentage=100.0,
                        root_cause_category="DUPLICATE_WEBHOOK",
                        severity="HIGH",
                    )
                ]
                evidence = [
                    MatchEvidence(
                        rule_name="DUPLICATE_RECORD_DETECTION",
                        algorithm_pass=MatchAlgorithmPass.PASS_6_DUPLICATE_DETECTION,
                        score_contribution=98.0,
                        explanation=(
                            f"Duplicate transaction detected: '{t_ext}' duplicates '{dup_ext}' "
                            f"with identical amount {t.currency} {t.amount} and reference '{ref}'."
                        ),
                        details={"duplicated_txn_id": dup_ext},
                    )
                ]
                results.append(
                    MatchCandidateResult(
                        match_type="DUPLICATE_PAIR",
                        match_status=MatchStatus.DUPLICATE,
                        confidence_score=98.0,
                        confidence_level=ConfidenceLevel.HIGH,
                        algorithm_pass=MatchAlgorithmPass.PASS_6_DUPLICATE_DETECTION,
                        source_transaction_id=t.id,
                        matched_transaction_id=dup_t.id,
                        evidence=evidence,
                        discrepancies=discrepancies,
                    )
                )
            else:
                seen_txns[key] = t

        # -------------------------------------------------------------
        # PASS 7: Orphan / Unmatched / Missing Exceptions
        # -------------------------------------------------------------
        for t in transactions:
            t_status = str(getattr(t, "status", "") or "").upper()
            t_desc = str(getattr(t, "description", "") or "").upper()
            is_unmatched_candidate = (
                t_status in ["UNMATCHED", "PENDING"]
                or any(k in t_desc for k in ["FEE", "CHARGE", "MAINTENANCE", "INTEREST", "ORPHAN", "PENALTY"])
            )
            if t.id not in matched_txn_ids and is_unmatched_candidate:
                t_ext = cls.get_txn_ext_id(t)
                discrepancies = [
                    DiscrepancyDetail(
                        discrepancy_type=DiscrepancyType.MISSING_ENTRY,
                        field_name="transaction_id",
                        source_value=t_ext,
                        matched_value=None,
                        difference_numeric=float(t.amount),
                        root_cause_category="UNRECORDED_EXPENSE",
                        severity="MEDIUM",
                    )
                ]
                evidence = [
                    MatchEvidence(
                        rule_name="ORPHAN_UNMATCHED_RECORD",
                        algorithm_pass=MatchAlgorithmPass.PASS_7_ORPHAN_EXCEPTION,
                        score_contribution=0.0,
                        explanation=(
                            f"Unmatched record in {t.source_type} feed: '{t_ext}' "
                            f"({t.currency} {t.amount}) has no corresponding entry across any source."
                        ),
                        details={"source_type": t.source_type, "amount": float(t.amount)},
                    )
                ]
                results.append(
                    MatchCandidateResult(
                        match_type="TXN_TO_TXN",
                        match_status=MatchStatus.MISSING_RECORD,
                        confidence_score=0.0,
                        confidence_level=ConfidenceLevel.LOW,
                        algorithm_pass=MatchAlgorithmPass.PASS_7_ORPHAN_EXCEPTION,
                        source_transaction_id=t.id,
                        evidence=evidence,
                        discrepancies=discrepancies,
                    )
                )

        return results
