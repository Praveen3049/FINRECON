import os
import re
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from app.core.config import settings
from app.core.logging import logger

FINANCIAL_FORENSIC_PROMPT = """You are FinRecon AI, an elite Senior Financial Forensic Investigator and Corporate Reconciliation Auditor.
You analyze complex multi-source corporate and decentralized financial records across:
1. Bank Feeds (HDFC, SBI, ICICI, Citi, NEFT, RTGS, IMPS, SWIFT, Fedwire)
2. Payment Gateways (Stripe, Razorpay, Adyen, PayPal, fee netting, chargebacks, rolling reserves)
3. ERP & Accounting Ledgers (NetSuite, SAP, QuickBooks, General Ledger accounts)
4. Commercial Invoices (Tax IDs, GSTIN, Sec 194C/J TDS deductions, line items)
5. Blockchain Ledgers (Ethereum, Polygon, Bitcoin, Solana, gas fees, slippage, on-chain TX hashes)

Guidelines for your responses:
- Tone: Professional, authoritative, audit-compliant, data-focused enterprise fintech.
- Formatting: Use structured Markdown with clear headings, bullet points, and monetary figures formatted clearly (e.g. ₹ or $ with comma separation).
- Structure:
  ### Executive Summary
  Brief, high-impact assessment.

  ### Verified Reconciliation Facts
  Specific identifiers, counterparties, dates, and amounts.

  ### Mathematical Variance & Root Cause
  Step-by-step breakdown of fee netting, tax withholding, settlement lag, or slippage.

  ### Recommended Action & ERP Journal Entries
  Audit-compliant instructions and exact Debit/Credit journal lines with standard account names when applicable.
"""


class ChatGPTClient:
    """
    OpenAI ChatGPT Integration for FinRecon AI Assistant.
    Provides natural language explanations, forensic investigation of exceptions,
    and automated ERP journal adjustment proposals.
    """

    _runtime_key: Optional[str] = None
    _runtime_model: Optional[str] = None

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        if cls._runtime_key:
            return cls._runtime_key
        if settings.OPENAI_API_KEY:
            return settings.OPENAI_API_KEY
        return os.environ.get("OPENAI_API_KEY", None)

    @classmethod
    def get_model(cls) -> str:
        if cls._runtime_model:
            return cls._runtime_model
        return getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    def is_configured(cls) -> bool:
        key = cls.get_api_key()
        return bool(key and len(key.strip()) > 10 and not key.startswith("sk-placeholder"))

    @classmethod
    def set_api_key(cls, key: str, model: Optional[str] = None, persist_to_env: bool = True) -> bool:
        """
        Dynamically update OpenAI API key and optionally save to .env
        """
        clean_key = key.strip()
        cls._runtime_key = clean_key
        if model:
            cls._runtime_model = model.strip()

        if persist_to_env:
            try:
                env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
                lines = []
                key_found = False
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                new_lines = []
                for line in lines:
                    if line.startswith("OPENAI_API_KEY="):
                        new_lines.append(f'OPENAI_API_KEY="{clean_key}"\n')
                        key_found = True
                    elif model and line.startswith("OPENAI_MODEL="):
                        new_lines.append(f'OPENAI_MODEL="{model}"\n')
                    else:
                        new_lines.append(line)

                if not key_found:
                    new_lines.append(f'OPENAI_API_KEY="{clean_key}"\n')
                    if model:
                        new_lines.append(f'OPENAI_MODEL="{model}"\n')

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception as e:
                logger.warning(f"Failed to persist OPENAI_API_KEY to .env: {e}")

        return True

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        key = cls.get_api_key()
        has_key = bool(key and len(key.strip()) > 10)
        preview = None
        if has_key:
            preview = f"{key[:7]}...{key[-4:]}"

        return {
            "is_configured": has_key,
            "provider": "OpenAI ChatGPT",
            "model": cls.get_model(),
            "key_preview": preview,
        }

    @classmethod
    def chat(
        cls,
        query: str,
        system_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send a conversation message to ChatGPT with financial forensic context.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "answer": (
                    "### ChatGPT Integration Ready\n\n"
                    "OpenAI ChatGPT integration is ready, but an **OpenAI API Key** has not been provided yet.\n\n"
                    "**To activate live ChatGPT:**\n"
                    "1. Click the **'Configure Key'** button above or provide your OpenAI API key.\n"
                    "2. Or add `OPENAI_API_KEY=sk-...` to your `backend/.env` file.\n\n"
                    "The assistant will automatically switch to live **GPT-4o** reasoning once your key is supplied."
                ),
                "model": cls.get_model(),
                "provider": "FinRecon Local Engine (Pending ChatGPT Key)",
                "success": False,
            }

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=getattr(settings, "OPENAI_BASE_URL", None),
                timeout=getattr(settings, "OPENAI_TIMEOUT_SECONDS", 30.0),
            )

            messages = [{"role": "system", "content": FINANCIAL_FORENSIC_PROMPT}]

            if system_context:
                messages.append({
                    "role": "system",
                    "content": f"Database Grounding & Verified Financial Context:\n{system_context}",
                })

            if conversation_history:
                for msg in conversation_history[-6:]:  # Keep recent context window
                    if msg.get("role") in ("user", "assistant") and msg.get("content"):
                        messages.append({"role": msg["role"], "content": msg["content"]})

            messages.append({"role": "user", "content": query})

            model_name = cls.get_model()
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=1500,
            )

            answer_text = response.choices[0].message.content or ""

            return {
                "answer": answer_text,
                "model": model_name,
                "provider": f"OpenAI ChatGPT ({model_name})",
                "success": True,
                "tokens_used": response.usage.total_tokens if response.usage else None,
            }

        except Exception as e:
            logger.error(f"OpenAI ChatGPT API error: {e}")
            return {
                "answer": (
                    f"### OpenAI API Notice\n\n"
                    f"Encountered an issue communicating with OpenAI: `{str(e)}`\n\n"
                    f"Please check your API key validity, quota limits, or network connectivity."
                ),
                "model": cls.get_model(),
                "provider": "OpenAI Error Fallback",
                "success": False,
            }

    @classmethod
    def investigate_case(
        cls,
        evidence: Dict[str, Any],
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive forensic investigation report for a reconciliation case using ChatGPT.
        Returns structured fields matching the reconciliation case investigation model.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return {
                "success": False,
                "error": "OpenAI API Key not configured",
            }

        evidence_str = json.dumps(evidence, indent=2, default=str)
        prompt_content = (
            f"ANALYST QUESTION: \"{question or 'Why was this transaction flagged and what are the verified facts?'}\"\n\n"
            f"STRUCTURED RECONCILIATION EVIDENCE:\n```json\n{evidence_str}\n```\n"
        )

        system_prompt = """You are FinRecon AI, an elite Senior Financial Forensic Investigator and Reconciliation Auditor.
Your job is to explain the structured financial evidence provided by the deterministic engine.

MANDATORY RULES:
1. The deterministic reconciliation engine is the sole source of truth. DO NOT invent or alter transaction data.
2. DO NOT change confidence scores, match statuses, or amounts.
3. Clearly explain root causes (e.g. gateway fees withheld at source, TDS tax deductions, weekend ACH settlement lag, on-chain token price slippage, or duplicate bank debits).
4. For crypto: distinguish on-chain gas fees and fiat slippage from fraud. Do not claim fraud unless application evidence specifies it.

Return ONLY a valid JSON object with these exact keys:
{
  "summary": "Concise 1-2 sentence executive overview",
  "why_flagged": "Exact technical/financial reason this was flagged or matched",
  "explanation": "Clear plain-English forensic breakdown of numbers, calculations, dates, counterparties, and fees formatted with clean Markdown headings and tables if helpful",
  "reviewer_attention": "The single most important fact or risk the reviewer must check",
  "suggested_next_checks": ["Audit check 1", "Audit check 2", "Audit check 3"]
}"""

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=getattr(settings, "OPENAI_BASE_URL", None),
                timeout=getattr(settings, "OPENAI_TIMEOUT_SECONDS", 30.0),
            )
            model_name = cls.get_model()

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_content},
                ],
                temperature=0.2,
                max_tokens=1800,
            )

            raw_text = (response.choices[0].message.content or "").strip()
            clean_text = raw_text
            if clean_text.startswith("```"):
                clean_text = re.sub(r"^```[a-zA-Z]*\n?", "", clean_text)
                clean_text = re.sub(r"\n?```$", "", clean_text).strip()

            parsed = {}
            try:
                parsed = json.loads(clean_text)
            except Exception:
                pass

            return {
                "success": True,
                "model": model_name,
                "provider": f"OpenAI ChatGPT ({model_name})",
                "summary": parsed.get("summary") if isinstance(parsed, dict) else None,
                "why_flagged": parsed.get("why_flagged") if isinstance(parsed, dict) else None,
                "explanation": parsed.get("explanation") if isinstance(parsed, dict) else raw_text,
                "reviewer_attention": parsed.get("reviewer_attention") if isinstance(parsed, dict) else None,
                "suggested_next_checks": parsed.get("suggested_next_checks") if isinstance(parsed, dict) and isinstance(parsed.get("suggested_next_checks"), list) else None,
                "raw_report": raw_text,
            }
        except Exception as e:
            logger.error(f"ChatGPT case investigation error: {e}")
            return {
                "success": False,
                "error": str(e),
            }

