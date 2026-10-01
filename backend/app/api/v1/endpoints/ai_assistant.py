from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_assistant.models import (
    AIStatusResponse,
    ChatQueryRequest,
    ChatQueryResponse,
    ConfigureAIKeyRequest,
    ExplanationResponse,
    InvestigationCaseRequest,
    InvestigationExplanationResponse,
    PrebuiltPrompt,
)
from app.services.ai_assistant.service import AIAssistantService
from app.services.ai_assistant.chatgpt_client import ChatGPTClient
from app.services.ai_assistant.nova_client import NovaClient

router = APIRouter()


@router.get("/status", response_model=AIStatusResponse)
def get_ai_status():
    """
    Returns live connectivity status of ChatGPT and Nova LLM engines.
    """
    cg_status = ChatGPTClient.get_status()
    nova_configured = NovaClient().is_configured
    openai_configured = cg_status["is_configured"]

    active_engine = "Deterministic Financial Engine"
    if nova_configured:
        active_engine = "Nova AI"
    elif openai_configured:
        active_engine = f"OpenAI ChatGPT ({cg_status['model']})"

    return AIStatusResponse(
        openai_configured=openai_configured,
        model=cg_status["model"],
        provider=cg_status["provider"],
        key_preview=cg_status["key_preview"],
        nova_configured=nova_configured,
        active_engine=active_engine,
    )


@router.post("/configure-key", response_model=AIStatusResponse)
def configure_ai_key(request: ConfigureAIKeyRequest):
    """
    Sets OpenAI API Key and model dynamically without server restart.
    """
    if not request.api_key or len(request.api_key.strip()) < 10:
        raise HTTPException(status_code=400, detail="Invalid API key provided")

    ChatGPTClient.set_api_key(key=request.api_key, model=request.model)
    return get_ai_status()


@router.get("/prompts", response_model=List[PrebuiltPrompt])
def get_prebuilt_prompts():
    """
    Returns curated financial reconciliation inquiry prompts.
    """
    return AIAssistantService.get_prebuilt_prompts()


@router.post("/chat", response_model=ChatQueryResponse)
def chat_with_assistant(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Ask any reconciliation, variance, or accounting question with grounded database context.
    """
    return AIAssistantService.answer_chat_query(db, request.query, request.case_id)


@router.post("/explain/case/{case_id}", response_model=ExplanationResponse)
def explain_reconciliation_case(
    case_id: str,
    db: Session = Depends(get_db),
):
    """
    Generates a structured plain-English explanation of a reconciliation case
    partitioned into verified FACTS, mathematical CALCULATIONS, and SUGGESTED ERP adjustments.
    """
    res = AIAssistantService.explain_case(db, case_id)
    if not res.case_id:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")
    return res


@router.post("/explain/discrepancy/{discrepancy_id}", response_model=ExplanationResponse)
def explain_discrepancy(
    discrepancy_id: str,
    db: Session = Depends(get_db),
):
    """
    Generates a deep-dive explanation of a specific discrepancy and root cause.
    """
    res = AIAssistantService.explain_discrepancy(db, discrepancy_id)
    return res


@router.post("/explain", response_model=InvestigationExplanationResponse)
async def explain_case_investigation(
    request: InvestigationCaseRequest,
    db: Session = Depends(get_db),
):
    """
    Primary FIN-26 Nova Investigation Endpoint.
    Translates structured reconciliation evidence into:
    - Summary
    - Why it was flagged
    - Matching evidence
    - Discrepancies
    - Reviewer attention
    - Suggested next checks
    """
    res = await AIAssistantService.investigate_case_with_nova(
        db,
        request.reconciliation_case_id,
        request.question,
    )
    if res.status == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"Case '{request.reconciliation_case_id}' not found")
    return res
