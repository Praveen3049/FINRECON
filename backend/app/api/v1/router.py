from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, database_summary, ingestion, normalization, entities, reconciliation, crypto, exceptions, audit, ai_assistant

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Access Control"])
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(database_summary.router, prefix="", tags=["Database"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Ingestion"])
api_router.include_router(normalization.router, prefix="/normalization", tags=["Normalization"])
api_router.include_router(entities.router, prefix="/entities", tags=["Entities"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["Reconciliation"])
api_router.include_router(crypto.router, prefix="/crypto", tags=["Crypto"])
api_router.include_router(exceptions.router, prefix="/exceptions", tags=["Exceptions"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit & Compliance"])
api_router.include_router(ai_assistant.router, prefix="/ai-assistant", tags=["AI Assistant & Explanations"])





