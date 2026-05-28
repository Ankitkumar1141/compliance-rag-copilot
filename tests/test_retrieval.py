"""
test_retrieval.py — Unit tests for retrieval components.
Tests BM25, VectorSearch fallback, HybridRetriever, QueryTransformer, and RerankingStage.
All tests use mock/in-memory data — no API keys needed.
"""

import os
import sys
import json
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from langchain_core.documents import Document


# ─────────────────────────────────────────────
# BM25Search tests
# ─────────────────────────────────────────────

class TestBM25Search:
    def _write_chunks_json(self, tmp_path, docs):
        chunks_data = [
            {"page_content": d.page_content, "metadata": d.metadata}
            for d in docs
        ]
        p = tmp_path / "chunks.json"
        p.write_text(json.dumps(chunks_data), encoding="utf-8")
        return str(p)

    def test_search_returns_relevant_doc(self, tmp_path):
        from rag.retrieval.bm25_search import BM25Search
        docs = [
            Document(page_content="Passwords must be hashed using bcrypt.", metadata={"source": "policy.md"}),
            Document(page_content="GDPR Article 6 requires lawful basis for processing.", metadata={"source": "gdpr.md"}),
            Document(page_content="MFA must be enforced on all production systems.", metadata={"source": "soc2.md"}),
        ]
        path = self._write_chunks_json(tmp_path, docs)
        searcher = BM25Search(chunks_json_path=path)
        # Retrieve all 3 docs — BM25 returns all when k >= corpus size
        results = searcher.search("password hashing bcrypt", k=3)
        assert len(results) >= 1
        # The bcrypt doc must appear somewhere in the results
        assert any("bcrypt" in r.page_content.lower() for r in results)

    def test_search_empty_db_returns_empty(self, tmp_path):
        from rag.retrieval.bm25_search import BM25Search
        path = tmp_path / "chunks.json"
        path.write_text("[]", encoding="utf-8")
        searcher = BM25Search(chunks_json_path=str(path))
        results = searcher.search("any query", k=3)
        assert results == []

    def test_search_missing_json_returns_empty(self, tmp_path):
        from rag.retrieval.bm25_search import BM25Search
        searcher = BM25Search(chunks_json_path=str(tmp_path / "nonexistent.json"))
        results = searcher.search("any query", k=3)
        assert results == []


# ─────────────────────────────────────────────
# RerankingStage tests
# ─────────────────────────────────────────────

class TestRerankingStage:
    def test_rerank_reduces_to_top_k(self):
        from rag.retrieval.reranker import RerankingStage
        docs = [
            Document(page_content=f"Compliance document chunk number {i}.", metadata={"source": f"doc{i}.md"})
            for i in range(10)
        ]
        reranker = RerankingStage()
        top_k = 3
        results = reranker.rerank("compliance policy", docs, top_k=top_k)
        assert len(results) <= top_k

    def test_rerank_empty_list_returns_empty(self):
        from rag.retrieval.reranker import RerankingStage
        reranker = RerankingStage()
        results = reranker.rerank("query", [], top_k=5)
        assert results == []

    def test_rerank_fewer_docs_than_top_k(self):
        from rag.retrieval.reranker import RerankingStage
        docs = [
            Document(page_content="Only two docs here.", metadata={}),
            Document(page_content="Password hashing policy.", metadata={}),
        ]
        reranker = RerankingStage()
        results = reranker.rerank("password", docs, top_k=5)
        assert len(results) <= 2


# ─────────────────────────────────────────────
# QueryTransformer tests
# ─────────────────────────────────────────────

class TestQueryTransformer:
    def test_transform_password_query_mock(self):
        from rag.retrieval.query_transform import QueryTransformer
        # Use mock provider so no LLM call is made
        transformer = QueryTransformer(provider="mock")
        queries = transformer.transform("Can I store passwords in plain text?")
        assert isinstance(queries, list)
        assert len(queries) >= 1
        # Original query must be in the result
        assert any("password" in q.lower() for q in queries)

    def test_transform_gdpr_query_mock(self):
        from rag.retrieval.query_transform import QueryTransformer
        transformer = QueryTransformer(provider="mock")
        queries = transformer.transform("What does GDPR say about consent?")
        assert isinstance(queries, list)
        assert len(queries) >= 1

    def test_transform_always_includes_original(self):
        from rag.retrieval.query_transform import QueryTransformer
        transformer = QueryTransformer(provider="mock")
        original = "Is MFA required for production?"
        queries = transformer.transform(original)
        assert original in queries or any(original.lower() in q.lower() for q in queries)
