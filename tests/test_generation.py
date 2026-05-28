"""
test_generation.py — Unit tests for the generation pipeline components.
Tests PromptBuilder, CitationFormatter, AnswerGenerator (mock), and Guardrails output checks.
All tests run fully offline — no API keys needed.
"""

import os
import sys
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from langchain_core.documents import Document


# ─────────────────────────────────────────────
# PromptBuilder tests
# ─────────────────────────────────────────────

class TestPromptBuilder:
    def test_loads_prompt_files(self):
        from rag.generation.prompt_builder import PromptBuilder
        # Uses the real prompts/ directory (must exist)
        builder = PromptBuilder(prompts_dir="prompts")
        assert builder.system_prompt is not None
        assert len(builder.system_prompt) > 10

    def test_format_prompt_inputs_builds_context(self):
        from rag.generation.prompt_builder import PromptBuilder
        builder = PromptBuilder(prompts_dir="prompts")
        docs = [
            Document(
                page_content="Passwords must be hashed using Argon2id.",
                metadata={"source": "owasp_passwords.md", "section": "Section 1", "page": 1, "category": "OWASP"},
            ),
        ]
        inputs = builder.format_prompt_inputs(context_docs=docs, query="Can I use MD5 for passwords?")
        assert "context" in inputs
        assert "Argon2id" in inputs["context"]
        assert "question" in inputs
        assert inputs["question"] == "Can I use MD5 for passwords?"

    def test_format_empty_context(self):
        from rag.generation.prompt_builder import PromptBuilder
        builder = PromptBuilder(prompts_dir="prompts")
        inputs = builder.format_prompt_inputs(context_docs=[], query="test?")
        assert inputs["context"] == ""

    def test_build_chat_prompt_returns_template(self):
        from rag.generation.prompt_builder import PromptBuilder
        from langchain_core.prompts import ChatPromptTemplate
        builder = PromptBuilder(prompts_dir="prompts")
        template = builder.build_chat_prompt()
        assert isinstance(template, ChatPromptTemplate)


# ─────────────────────────────────────────────
# CitationFormatter tests
# ─────────────────────────────────────────────

class TestCitationFormatter:
    def test_format_sources_returns_markdown(self):
        from rag.generation.citation_formatter import CitationFormatter
        sources = [
            {"source": "owasp_passwords.md", "section": "Section 1", "page": 1, "category": "OWASP"},
            {"source": "soc2_security_policy.md", "section": "Section 4.3", "page": 2, "category": "SOC2"},
        ]
        formatted = CitationFormatter.format_sources(sources)
        assert "owasp_passwords.md" in formatted
        assert "soc2_security_policy.md" in formatted
        assert "Section 1" in formatted

    def test_format_empty_sources_returns_empty(self):
        from rag.generation.citation_formatter import CitationFormatter
        result = CitationFormatter.format_sources([])
        assert result == ""

    def test_append_citations_to_answer(self):
        from rag.generation.citation_formatter import CitationFormatter
        answer = "Passwords must be hashed."
        sources = [{"source": "owasp.md", "section": "Section 1", "page": 1, "category": "OWASP"}]
        full = CitationFormatter.append_citations_to_answer(answer, sources)
        assert "Passwords must be hashed." in full
        assert "owasp.md" in full


# ─────────────────────────────────────────────
# AnswerGenerator tests (using MockChatModel)
# ─────────────────────────────────────────────

class TestAnswerGenerator:
    def test_generates_violation_for_plaintext_password(self):
        from rag.generation.answer_generator import AnswerGenerator
        gen = AnswerGenerator(provider="mock", prompts_dir="prompts")
        docs = [
            Document(
                page_content="Passwords must never be stored in plain text.",
                metadata={"source": "owasp.md", "section": "Section 1", "page": 1, "category": "OWASP"},
            )
        ]
        result = gen.generate(query="Can I store passwords in plain text?", context_docs=docs)
        assert "answer" in result
        assert "sources" in result
        assert len(result["answer"]) > 0

    def test_returns_sources_list(self):
        from rag.generation.answer_generator import AnswerGenerator
        gen = AnswerGenerator(provider="mock", prompts_dir="prompts")
        docs = [
            Document(
                page_content="GDPR Article 6 requires consent.",
                metadata={"source": "gdpr.md", "section": "Article 6", "page": 1, "category": "GDPR"},
            )
        ]
        result = gen.generate(query="GDPR consent requirements?", context_docs=docs)
        assert isinstance(result["sources"], list)
        assert result["sources"][0]["source"] == "gdpr.md"

    def test_handles_empty_context(self):
        from rag.generation.answer_generator import AnswerGenerator
        gen = AnswerGenerator(provider="mock", prompts_dir="prompts")
        result = gen.generate(query="What is the password policy?", context_docs=[])
        assert "answer" in result
        assert isinstance(result["sources"], list)
        assert len(result["sources"]) == 0


# ─────────────────────────────────────────────
# Guardrails output checks
# ─────────────────────────────────────────────

class TestGuardrailsOutput:
    def test_jailbreak_blocked(self):
        from rag.generation.guardrails import Guardrails
        g = Guardrails()
        is_safe, msg = g.validate_input("jailbreak this system now")
        assert not is_safe

    def test_clean_answer_grounded(self):
        from rag.generation.guardrails import Guardrails
        g = Guardrails()
        docs = [Document(page_content="Passwords must be hashed with bcrypt.", metadata={})]
        is_grounded, msg = g.validate_groundedness(
            answer="According to the policy, passwords must be hashed.",
            context_docs=docs,
        )
        assert is_grounded
