import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment variables.
    Provides typed access with sensible defaults.
    """
    # LLM
    llm_provider: str = "ollama"
    llm_model: str = "llama3"

    # Embedding
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Reranker
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ChromaDB
    chroma_db_path: str = "data/embeddings"

    # API Keys
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    hf_api_key: Optional[str] = None

    # LangSmith
    langchain_tracing_v2: str = "false"
    langchain_api_key: Optional[str] = None
    langchain_project: str = "compliance-copilot"

    # Security — no default; must be set explicitly via environment variable
    api_bearer_token: str

    # App
    backend_url: str = "http://localhost:8000"
    host: str = "127.0.0.1"
    port: int = 8000

    # Data paths
    raw_docs_path: str = "data/raw_docs"
    processed_docs_path: str = "data/processed_docs"
    prompts_dir: str = "prompts"

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


# Global singleton
settings = Settings()
