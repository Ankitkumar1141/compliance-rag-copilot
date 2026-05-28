"""
main.py — FastAPI application entry point for the Compliance Copilot backend.
"""

import sys
import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Bootstrap sys.path so relative imports work from anywhere ──
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.backend.config import settings
from app.backend.routes import router
from rag.monitoring.langsmith_tracker import init_langsmith
from rag.monitoring.logging_config import setup_logging

# ── Initialise logging ──
setup_logging()
logger = logging.getLogger("compliance_copilot")

# ── Initialise LangSmith tracing (no-op if key not set) ──
init_langsmith()

# ── FastAPI app ──
app = FastAPI(
    title="Compliance Copilot API",
    description=(
        "A RAG-powered Compliance Copilot that answers questions about GDPR, SOC2, "
        "ISO27001, OWASP, and internal engineering policies with source citations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ──
app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "Compliance Copilot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    _dev_reload = os.getenv("DEV_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "app.backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=_dev_reload,
        log_level="info",
    )
