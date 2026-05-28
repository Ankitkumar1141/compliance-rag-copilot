"""
conftest.py — Shared pytest fixtures and configuration for all test modules.
"""

import os
import sys
import json
import pytest

# Ensure project root is on sys.path regardless of where pytest is invoked from
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """
    Set environment variables for test runs so no real API keys are needed.
    Uses the mock LLM provider and local embeddings.
    """
    os.environ.setdefault("LLM_PROVIDER", "mock")
    os.environ.setdefault("EMBEDDING_PROVIDER", "local")
    os.environ.setdefault("CHROMA_DB_PATH", "data/embeddings")
    os.environ.setdefault("API_BEARER_TOKEN", "compliance_secret_token_123")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
    yield


@pytest.fixture
def sample_docs():
    """Returns a small list of LangChain Documents for use in tests."""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="Passwords must be hashed using Argon2id or bcrypt. Plain text storage is prohibited.",
            metadata={"source": "owasp_passwords.md", "section": "Section 1", "page": 1, "category": "OWASP Security Guidelines"},
        ),
        Document(
            page_content="GDPR Article 6 requires a lawful basis for processing personal data including consent.",
            metadata={"source": "gdpr_article6.md", "section": "Article 6", "page": 1, "category": "GDPR"},
        ),
        Document(
            page_content="Company Security Policy Section 4.3: All passwords must be stored using a one-way hash with salt.",
            metadata={"source": "soc2_security_policy.md", "section": "Section 4.3", "page": 2, "category": "SOC2"},
        ),
    ]


@pytest.fixture
def chunks_json_file(tmp_path, sample_docs):
    """Creates a temporary chunks.json file with sample documents."""
    data = [
        {"page_content": d.page_content, "metadata": d.metadata}
        for d in sample_docs
    ]
    f = tmp_path / "chunks.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return str(f)
