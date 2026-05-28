# Compliance Copilot — RAG Project

A production-ready, RAG-powered Compliance Copilot that answers questions about GDPR, SOC2, ISO27001, OWASP guidelines, and internal engineering policies — with source citations, violation detection, and guardrails.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.ai) for local LLM inference

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env to set your LLM_PROVIDER (ollama / groq / huggingface)
# and optionally GROQ_API_KEY or HF_API_KEY
```

### 3. Ingest compliance documents

Place your PDFs, DOCX, Markdown, or TXT files in `data/raw_docs/`, then run:

```bash
python -m rag.ingestion.pipeline
```

> Mock compliance docs (GDPR, OWASP, SOC2) are already seeded in `data/raw_docs/` for testing.

### 4. Start the FastAPI backend

```bash
python -m app.backend.main
# or
uvicorn app.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. Start the Streamlit frontend

```bash
streamlit run app/frontend/app.py
```

Open http://localhost:8501 in your browser.

---

## 🛠 LLM Provider Configuration

Set `LLM_PROVIDER` in your `.env`:

| Provider | Value | Notes |
|---|---|---|
| Ollama (local) | `ollama` | Install Ollama, run `ollama pull llama3` |
| Groq | `groq` | Set `GROQ_API_KEY` (free tier) |
| HuggingFace | `huggingface` | Set `HF_API_KEY` (free token) |
| Mock (offline) | `mock` | Works with no API key — for testing only |

---

## 🐳 Docker Deployment

```bash
cd deployment
docker-compose up --build
```

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📁 Project Structure

```
compliance-rag-copilot/
├── app/
│   ├── frontend/app.py          # Streamlit UI
│   └── backend/
│       ├── main.py              # FastAPI entry point
│       ├── routes.py            # API routes (/chat, /upload, /health)
│       ├── auth.py              # Bearer token auth
│       └── config.py            # Pydantic settings
├── data/
│   ├── raw_docs/                # Source compliance documents
│   ├── processed_docs/          # Chunked JSON cache + benchmark
│   └── embeddings/              # ChromaDB vector store
├── models/
│   ├── llm_factory.py           # LLM factory (Ollama/Groq/HF/mock)
│   ├── embedding_models.py      # Embedding factory (local/OpenAI)
│   └── reranker_factory.py      # CrossEncoder reranker
├── prompts/                     # Versioned prompt templates
├── rag/
│   ├── ingestion/               # Load → Chunk → Enrich → Embed
│   ├── retrieval/               # Hybrid (Vector + BM25) + Reranking
│   ├── generation/              # Prompt → LLM → Citations + Guardrails
│   ├── evaluation/              # RAGAS eval + benchmark dataset
│   └── monitoring/              # LangSmith + structured logging
├── tests/                       # Pytest unit + integration tests
├── deployment/                  # Dockerfile + docker-compose
└── requirements.txt
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📊 API Reference

All endpoints require `Authorization: Bearer <API_BEARER_TOKEN>`.

### `POST /api/v1/chat`
```json
{
  "query": "Can I store customer passwords in plain text?",
  "chat_history": "",
  "top_k": 5
}
```
Returns: answer, sources with citations, latency, guardrail warnings.

### `POST /api/v1/upload`
Upload a compliance document (PDF/DOCX/MD/TXT) — triggers automatic ingestion.

### `GET /api/v1/health`
Returns backend status, LLM provider, and vector DB readiness.
