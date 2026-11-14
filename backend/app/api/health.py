from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database.session import get_db
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """
    Checks operational availability of:
    - Backend API
    - Database Connectivity
    - Redis / Background Worker Broker
    - AI Provider Configuration
    """
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    redis_status = "unavailable"
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1.0)
        r.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "standalone_fallback (in-process queue active)"

    ai_configured = bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)
    ai_status = {
        "provider": settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
        "is_configured": ai_configured,
        "mode": "live_api" if ai_configured else "heuristic_fallback",
        "warning": None if ai_configured else "No LLM API key detected. Heuristic fallback extractor active.",
    }

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "backend": "healthy",
        "database": db_status,
        "background_queue": redis_status,
        "ai_provider": ai_status,
        "environment": settings.ENVIRONMENT,
    }

