"""
routes.py — FastAPI route definitions for the Compliance Copilot API.

Endpoints:
  POST /api/v1/chat    — Answer a compliance question with citations
  POST /api/v1/upload  — Upload a document and trigger ingestion
  GET  /api/v1/health  — Health check
"""

import os
import sys
import time
import shutil
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.backend.auth import verify_token
from app.backend.config import settings

logger = logging.getLogger("compliance_copilot")

router = APIRouter(prefix="/api/v1", tags=["Compliance Copilot"])


# ─────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="The compliance question to answer.")
    chat_history: Optional[str] = Field(default="", description="Optional multi-turn chat history context.")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of source chunks to retrieve.")


class SourceCitation(BaseModel):
    source: str
    section: str
    page: int
    category: str


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceCitation]
    guardrail_warning: Optional[str] = None
    latency_ms: float


class UploadResponse(BaseModel):
    filename: str
    message: str
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    embedding_provider: str
    vector_db_ready: bool


# ─────────────────────────────────────────────
# Lazy-loaded singletons (initialized on first request)
# ─────────────────────────────────────────────

_hybrid_retriever = None
_reranker = None
_query_transformer = None
_answer_generator = None
_guardrails = None
_metrics_logger = None


def _get_pipeline_components():
    global _hybrid_retriever, _reranker, _query_transformer, _answer_generator, _guardrails, _metrics_logger

    if _answer_generator is None:
        try:
            from rag.retrieval.hybrid_retriever import HybridRetriever
            from rag.retrieval.reranker import RerankingStage
            from rag.retrieval.query_transform import QueryTransformer
            from rag.generation.answer_generator import AnswerGenerator
            from rag.generation.guardrails import Guardrails
            from rag.monitoring.logging_config import QueryMetricsLogger

            _hybrid_retriever = HybridRetriever(
                persist_dir=settings.chroma_db_path,
                chunks_json_path=os.path.join(settings.processed_docs_path, "chunks.json"),
            )
            _reranker = RerankingStage()
            _query_transformer = QueryTransformer(provider=settings.llm_provider, model_name=settings.llm_model)
            _answer_generator = AnswerGenerator(
                provider=settings.llm_provider,
                model_name=settings.llm_model,
                prompts_dir=settings.prompts_dir,
            )
            _guardrails = Guardrails()
            _metrics_logger = QueryMetricsLogger()
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline components: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"RAG pipeline not ready: {str(e)}. Ensure documents have been ingested first.",
            )

    return _hybrid_retriever, _reranker, _query_transformer, _answer_generator, _guardrails, _metrics_logger


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, summary="Health Check")
async def health_check():
    """Returns the service health status and configuration details."""
    db_ready = os.path.exists(settings.chroma_db_path)
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
        vector_db_ready=db_ready,
    )


@router.post("/chat", response_model=ChatResponse, summary="Ask Compliance Question")
async def chat(request: ChatRequest, token: str = Depends(verify_token)):
    """
    Primary endpoint. Accepts a compliance question, runs hybrid retrieval + reranking,
    then generates a cited answer with guardrail checks.
    """
    start_time = time.time()
    from rag.generation.citation_formatter import CitationFormatter

    retriever, reranker, transformer, generator, guardrails, metrics_logger = _get_pipeline_components()

    # 1. Input Guardrail
    is_safe, injection_msg = guardrails.validate_input(request.query)
    if not is_safe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=injection_msg)

    # 2. Query Transformation (expansion)
    transformed_queries = transformer.transform(request.query)
    logger.info(f"Query transformed into {len(transformed_queries)} sub-queries.")

    # 3. Hybrid Retrieval — retrieve for each sub-query, deduplicate
    all_docs = []
    seen_contents = set()
    for q in transformed_queries:
        docs = retriever.retrieve(q, top_n=15)
        for doc in docs:
            content_key = doc.page_content[:100]
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                all_docs.append(doc)

    # 4. Reranking
    top_docs = reranker.rerank(request.query, all_docs, top_k=request.top_k)

    # 5. Answer Generation
    result = generator.generate(
        query=request.query,
        context_docs=top_docs,
        chat_history=request.chat_history or "",
    )

    answer = result["answer"]
    sources = result["sources"]

    # 6. Output Guardrail
    is_grounded, grounding_warning = guardrails.validate_groundedness(answer, top_docs)

    # 7. Metrics Logging
    latency_ms = (time.time() - start_time) * 1000
    is_violation = "[POLICY VIOLATION" in answer.upper()

    metrics_logger.log_query(
        query=request.query,
        latency_ms=latency_ms,
        num_chunks=len(top_docs),
        sources=sources,
        is_violation=is_violation,
        llm_provider=settings.llm_provider,
    )

    return ChatResponse(
        query=request.query,
        answer=answer,
        sources=[SourceCitation(**s) for s in sources],
        guardrail_warning=grounding_warning if not is_grounded else None,
        latency_ms=round(latency_ms, 2),
    )


@router.post("/upload", response_model=UploadResponse, summary="Upload Compliance Document")
async def upload_document(file: UploadFile = File(...), token: str = Depends(verify_token)):
    """
    Accepts a compliance document upload (PDF, DOCX, MD, TXT),
    saves it to raw_docs, and re-runs the ingestion pipeline.
    """
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save uploaded file
    os.makedirs(settings.raw_docs_path, exist_ok=True)
    save_path = os.path.join(settings.raw_docs_path, file.filename)

    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Uploaded file saved: {save_path}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # Re-run ingestion pipeline for the new file
    try:
        from rag.ingestion.pipeline import IngestionPipeline
        pipeline = IngestionPipeline(
            raw_dir=settings.raw_docs_path,
            processed_dir=settings.processed_docs_path,
        )
        chunks = pipeline.run(overwrite=False)
        chunks_created = len(chunks)

        # Reset cached pipeline components so retriever picks up new chunks
        global _hybrid_retriever, _answer_generator
        _hybrid_retriever = None
        _answer_generator = None

    except Exception as e:
        logger.error(f"Ingestion failed after upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File uploaded but ingestion failed: {str(e)}",
        )

    return UploadResponse(
        filename=file.filename,
        message="Document uploaded and ingested successfully.",
        chunks_created=chunks_created,
    )
