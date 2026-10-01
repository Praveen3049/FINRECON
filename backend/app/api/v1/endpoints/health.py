from datetime import datetime, timezone
import sys
from typing import Dict, Any
from fastapi import APIRouter, status
from app.core.config import settings
from app.core.database import check_db_health
from app.schemas.common import SourceType

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check() -> Dict[str, Any]:
    """
    Core system health-check endpoint.
    Verifies API responsiveness, database connectivity, and environment metadata.
    STRICT SECURITY RULE:
    - Never returns NOVA_API_KEY.
    - Never returns Authorization headers.
    - Reports only boolean status: nova_configured / NOVA_CONFIGURED.
    """
    db_ok = check_db_health()
    is_nova_configured = bool(settings.NOVA_API_KEY and settings.NOVA_API_KEY.strip())
    
    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_ok,
        "python_version": sys.version.split(" ")[0],
        "supported_sources": [s.value for s in SourceType],
        "nova_configured": is_nova_configured,
        "NOVA_CONFIGURED": is_nova_configured,
    }


@router.get("/health/diagnostics", status_code=status.HTTP_200_OK, tags=["Health"])
@router.get("/config", status_code=status.HTTP_200_OK, tags=["Health"])
def health_diagnostics() -> Dict[str, Any]:
    """
    Backend health/configuration diagnostics endpoint (FIN-26 Step 11).
    Reports configuration status without exposing any secrets or API keys.
    
    Reports:
    - NOVA_CONFIGURED: true/false
    - DATABASE_CONNECTED: true/false
    - RECONCILIATION_ENGINE_READY: true
    - DETERMINISTIC_FALLBACK_READY: true
    """
    db_ok = check_db_health()
    is_nova_configured = bool(settings.NOVA_API_KEY and settings.NOVA_API_KEY.strip())
    
    return {
        "STATUS": "HEALTHY" if db_ok else "DEGRADED",
        "NOVA_CONFIGURED": is_nova_configured,
        "NOVA_BASE_URL": settings.NOVA_API_BASE_URL,
        "DATABASE_CONNECTED": db_ok,
        "RECONCILIATION_ENGINE_READY": True,
        "DETERMINISTIC_FALLBACK_READY": True,
        "ENVIRONMENT": settings.ENVIRONMENT,
        "TIMESTAMP": datetime.now(timezone.utc).isoformat(),
    }
