import os
import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.database.session import engine, Base
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.documents import router as documents_router
from backend.app.api.verification import router as verification_router
from backend.app.api.search import router as search_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.analytics import router as analytics_router

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("documind")

# Initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DocuMind AI - Document Intelligence System API",
    description="Enterprise-grade AI Document Intelligence REST API for multi-format parsing, extraction, deterministic validation, cross-verification, and semantic search.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        logger.info(f"{request.method} {request.url.path} - Status {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred during processing. Please try again or check system logs.",
                "path": request.url.path,
            },
        )


# Include API Routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(verification_router, prefix="/api/verification", tags=["Verification"])
app.include_router(search_router, prefix="/api/search", tags=["Search"])
app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "DocuMind AI Document Intelligence Platform",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "status": "operational",
    }
