from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FactItem(BaseModel):
    field: str
    value: Any
    source: str
    description: Optional[str] = None


class CalculatedItem(BaseModel):
    metric: str
    value: Any
    formula: str
    interpretation: Optional[str] = None


class SuggestionItem(BaseModel):
    action: str
    justification: str
    confidence_level: str
    recommended_entry: Optional[str] = None


class JournalEntryLine(BaseModel):
    account_number: str
    account_name: str
    debit: float = 0.0
    credit: float = 0.0
    memo: str


class SuggestedJournalEntry(BaseModel):
    title: str
    memo: str
    reference: str
    total_debit: float
    total_credit: float
    lines: List[JournalEntryLine]


class ExplanationResponse(BaseModel):
    case_id: Optional[str] = None
    case_number: Optional[str] = None
    title: str
    status: str
    priority: str
    executive_summary: str
    facts: List[FactItem] = []
    calculated: List[CalculatedItem] = []
    suggestions: List[SuggestionItem] = []
    confidence_assessment: str
    suggested_journal_entry: Optional[SuggestedJournalEntry] = None
    audit_evidence_trail: List[str] = []


class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    case_id: Optional[str] = None


class ChatQueryResponse(BaseModel):
    query: str
    answer: str
    facts: List[FactItem] = []
    calculated: List[CalculatedItem] = []
    suggestions: List[SuggestionItem] = []
    suggested_journal_entry: Optional[SuggestedJournalEntry] = None
    related_cases: List[str] = []
    quick_followups: List[str] = []
    ai_provider: Optional[str] = "FinRecon Local Engine"


class PrebuiltPrompt(BaseModel):
    id: str
    category: str
    label: str
    prompt: str


class InvestigationCaseRequest(BaseModel):
    reconciliation_case_id: str = Field(..., description="ID or Case Number of the reconciliation case to explain")
    question: Optional[str] = Field("Why was this transaction flagged?", description="Analyst question to answer")


class InvestigationExplanationResponse(BaseModel):
    case_id: str
    case_number: str
    status: str
    confidence_score: float
    summary: str
    why_flagged: str
    matched_evidence: List[Dict[str, Any]] = []
    discrepancies: List[Dict[str, Any]] = []
    explanation: str
    reviewer_attention: str
    suggested_next_checks: List[str] = []
    facts: List[FactItem] = []
    calculated: List[CalculatedItem] = []
    suggested_journal_entry: Optional[SuggestedJournalEntry] = None
    ai_provider: str = "NOVA_AI"  # "CHATGPT", "NOVA_AI" or "DETERMINISTIC_FALLBACK"


class ConfigureAIKeyRequest(BaseModel):
    api_key: str = Field(..., min_length=10, description="OpenAI API key (sk-...)")
    model: Optional[str] = Field("gpt-4o-mini", description="OpenAI model (e.g. gpt-4o, gpt-4o-mini)")


class AIStatusResponse(BaseModel):
    openai_configured: bool
    model: str
    provider: str
    key_preview: Optional[str] = None
    nova_configured: bool
    active_engine: str
