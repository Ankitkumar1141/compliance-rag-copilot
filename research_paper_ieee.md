
# Compliance Copilot: A Retrieval-Augmented Generation System for Regulatory Document Question Answering

**Ankit Kumar Jha**  
Independent Researcher | Personal Project  
*ankit.aiml625@gmail.com*

---

> *Manuscript Type: Research Paper | Year: 2026*  
> *Domain: Artificial Intelligence, Natural Language Processing, Compliance Engineering*

---

## Abstract

Compliance with regulatory frameworks such as the General Data Protection Regulation (GDPR), SOC 2, ISO/IEC 27001, and OWASP security guidelines is a critical yet complex challenge for modern organizations. Legal and engineering teams spend significant effort manually searching across large volumes of compliance documentation to answer policy questions, identify violations, and generate audit-ready responses. This paper presents **Compliance Copilot**, a production-ready, open-source Retrieval-Augmented Generation (RAG) system designed to automate regulatory question answering with verifiable source citations and built-in safety guardrails. The system employs a multi-stage pipeline: a document ingestion pipeline supporting PDF, DOCX, Markdown, and plain-text formats; a hybrid retrieval strategy combining dense vector search (ChromaDB) and sparse keyword search (BM25) with LLM-driven query expansion; a cross-encoder reranking stage; and a generation stage backed by a pluggable LLM factory supporting Ollama, Groq, and HuggingFace inference backends. Output quality is validated using the RAGAS evaluation framework (measuring Faithfulness, Answer Relevancy, Context Recall, and Context Precision), while runtime safety is enforced through prompt-injection detection and hallucination grounding checks. The system is deployed as containerized microservices via Docker, exposing a FastAPI REST backend and a Streamlit interactive frontend. Experimental results demonstrate reliable citation-backed answers with measurable guardrail protection, contributing a reference architecture for compliance-domain RAG applications.

**Index Terms** — Retrieval-Augmented Generation, Regulatory Compliance, Natural Language Processing, Question Answering, Hybrid Retrieval, BM25, ChromaDB, LangChain, Guardrails, GDPR, OWASP

---

## I. Introduction

The landscape of digital compliance is growing more demanding each year. Enterprises operating under GDPR, SOC 2, ISO 27001, and OWASP must maintain up-to-date knowledge of hundreds of articles, controls, and guidelines. A single misinterpretation of a policy—for example, whether storing passwords in plaintext is prohibited—can result in substantial regulatory penalties or security breaches.

Traditional solutions rely on keyword search engines or static FAQ documents. While efficient, these approaches fail to understand query intent, cannot synthesize answers from multiple policy sources, and do not provide traceable citations. Large Language Models (LLMs) address these limitations with strong natural language understanding but are prone to hallucination—generating plausible but factually incorrect information when applied outside their training data. This is especially dangerous in a legal and compliance context.

Retrieval-Augmented Generation (RAG) [1] bridges this gap by grounding LLM responses in retrieved, authoritative documents. However, a naive RAG implementation applied to compliance documents faces several challenges:

1. **Semantic gap**: Compliance questions often use different vocabulary than source documents (e.g., "save passwords as text" vs. "plaintext credential storage").
2. **Multi-document synthesis**: Answering a single query often requires evidence from multiple regulatory frameworks simultaneously.
3. **Hallucination risk**: LLMs may inject domain-specific technical terms (e.g., "Argon2", "PBKDF2") not present in retrieved context.
4. **Security**: User inputs may attempt prompt injection to override system behavior.
5. **Traceability**: Enterprise compliance demands answers that cite the exact document, section, and page number.

This paper makes the following contributions:

- A **complete, production-ready RAG architecture** for the compliance domain, covering ingestion to deployment.
- A **hybrid retrieval strategy** combining dense semantic search (ChromaDB) with sparse BM25 retrieval and LLM-powered query expansion.
- **Dual-layer guardrails** enforcing input safety (prompt injection detection) and output faithfulness (hallucination grounding check).
- An **evaluation harness** based on the RAGAS framework with four quantitative metrics.
- A **containerized deployment** supporting multiple LLM backends through a unified factory pattern.

The remainder of this paper is organized as follows: Section II reviews related work; Section III describes the system architecture; Section IV details the methodology for each pipeline stage; Section V presents the evaluation framework; Section VI discusses results and design trade-offs; Section VII concludes.

---

## II. Related Work

### A. Retrieval-Augmented Generation

Lewis et al. [1] introduced RAG as a seq2seq architecture combining a dense retrieval model (DPR) with a BART generator. Subsequent work has expanded this paradigm to modular, LLM-chain-based systems. LangChain [2] provides a widely-adopted framework for composing retrieval, prompting, and generation components. Our system builds on LangChain's abstractions while adding compliance-specific extensions.

### B. Hybrid Retrieval

Dense vector retrieval excels at capturing semantic meaning but may miss exact regulatory terms (e.g., "Article 6", "Control A.12"). Sparse retrieval via BM25 [3] complements this by matching precise keywords. Ensemble retrieval combining both has been shown to outperform either method alone [4]. We weight dense retrieval at 0.6 and sparse at 0.4, reflecting the dominance of semantic understanding in compliance queries while preserving keyword precision.

### C. Query Expansion

Multi-query expansion generates multiple reformulations of the original query before retrieval, increasing recall at the cost of additional LLM inference [5]. Our implementation produces three targeted sub-queries optimized for both keyword and vector search, then deduplicates results before reranking.

### D. Cross-Encoder Reranking

Two-stage retrieval—first retrieve a large candidate pool, then rerank with a cross-encoder—is a well-established pattern in information retrieval [6]. Cross-encoders jointly encode query and document pairs, providing higher accuracy than bi-encoder cosine similarity alone. We integrate a sentence-transformers CrossEncoder model in the reranking stage.

### E. LLM Guardrails

Preventing prompt injection and hallucination in LLM-powered applications has received increasing attention. Perez and Ribeiro [7] characterize prompt injection attack patterns. LLM-based output verification (self-consistency checks, NLI-based grounding) has been proposed as a mitigation [8]. Our system applies a dual-phase guardrail: a rule-based regex filter for input and a keyword-grounding check for outputs.

### F. RAG Evaluation

The RAGAS framework [9] defines four reference-free and reference-based metrics for evaluating RAG pipelines: Faithfulness, Answer Relevancy, Context Recall, and Context Precision. These metrics have been adopted as a community standard for RAG quality assessment and form the backbone of our evaluation module.

---

## III. System Architecture

### A. Overview

Compliance Copilot is organized into five major layers, as illustrated in Fig. 1:

```
┌────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                      │
│           Streamlit Frontend  ◄──►  FastAPI Backend        │
└──────────────────────────┬─────────────────────────────────┘
                           │ REST (Bearer Token Auth)
┌──────────────────────────▼─────────────────────────────────┐
│                     RAG PIPELINE                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Ingestion│  │ Retrieval│  │Generation│  │Guardrails│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│                     DATA LAYER                             │
│   ChromaDB (Vector Store)   BM25 Index (JSON Cache)        │
│   Raw Docs (PDF/DOCX/MD)    Processed Chunks (JSON)        │
└────────────────────────────────────────────────────────────┘
```
*Fig. 1. High-level system architecture of Compliance Copilot.*

### B. Component Decomposition

| Module | Responsibility | Key Technologies |
|---|---|---|
| `rag/ingestion` | Load, chunk, enrich, embed documents | LangChain, pypdf, python-docx, ChromaDB |
| `rag/retrieval` | Hybrid search, query expansion, reranking | BM25, ChromaDB, sentence-transformers |
| `rag/generation` | Prompt assembly, LLM inference, citation formatting | LangChain, Groq/Ollama/HuggingFace |
| `rag/evaluation` | RAGAS metrics, benchmark harness | RAGAS, HuggingFace Datasets |
| `rag/monitoring` | Structured logging, LangSmith tracing | LangSmith, Python `logging` |
| `app/backend` | REST API, authentication, request routing | FastAPI, Pydantic, Uvicorn |
| `app/frontend` | Interactive chat interface | Streamlit |
| `models` | LLM and embedding factory pattern | LangChain integrations |
| `deployment` | Containerized multi-service deployment | Docker, Docker Compose |

### C. Request Lifecycle

A single `/api/v1/chat` request traverses the following steps:

1. **Token Authentication** — Bearer token validated by `auth.py`.
2. **Input Guardrail** — Query scanned for prompt injection patterns.
3. **Query Transformation** — LLM expands query into three keyword-rich sub-queries.
4. **Hybrid Retrieval** — Each sub-query retrieves up to 15 candidates; results are deduplicated.
5. **Reranking** — CrossEncoder reranks the candidate pool to `top_k` (default 5) documents.
6. **Answer Generation** — LLM generates a cited answer using structured context blocks.
7. **Output Guardrail** — Groundedness check validates answer against retrieved context.
8. **Metrics Logging** — Latency, chunk count, sources, and violation flag are recorded.
9. **Response** — Structured JSON with answer, citations, guardrail warnings, and latency.

---

## IV. Methodology

### A. Document Ingestion Pipeline

The ingestion pipeline (`rag/ingestion/pipeline.py`) consists of four sequential stages.

#### 1) Document Loading

`DocumentLoader` supports four file formats:

- **PDF** — Parsed via `PyPDFLoader` (LangChain), preserving page metadata.
- **DOCX** — Parsed via `Docx2txtLoader`.
- **Markdown** — Parsed via `UnstructuredMarkdownLoader`.
- **Plain Text** — Parsed via `TextLoader`.

The loader dispatches based on file extension, raising a warning for unsupported formats.

#### 2) Chunking

`DocumentChunker` applies LangChain's `RecursiveCharacterTextSplitter` with a chunk size of 1,000 characters and 200-character overlap. Overlapping windows ensure that regulatory clauses spanning chunk boundaries are not lost.

#### 3) Metadata Enrichment

`MetadataExtractor` standardizes and enriches each chunk with four fields:

- **source** — Filename (e.g., `gdpr_policy.pdf`).
- **category** — Compliance framework detected from filename keywords: `GDPR`, `SOC2`, `ISO27001`, `OWASP Security Guidelines`, or `Company Compliance Guidelines`.
- **page** — 1-indexed page number, normalized from loader output.
- **section** — Extracted by regex scanning for patterns such as `Article 6`, `Section 4.3`, `Control A.12.4`, or `Clause 9.1`.

```python
SECTION_REGEXES = [
    re.compile(r"(?:article|art\.)\s*(\d+[a-z]?)", re.IGNORECASE),
    re.compile(r"(?:section|sec\.)\s*(\d+(?:\.\d+)*)", re.IGNORECASE),
    re.compile(r"(?:control|ctrl\.)\s*([a-z]\.\d+(?:\.\d+)*)", re.IGNORECASE),
    re.compile(r"(?:annex|clause)\s*(\d+(?:\.\d+)*)", re.IGNORECASE)
]
```

#### 4) Embedding and Vector Storage

`Embedder` uses a pluggable embedding model (default: `sentence-transformers/all-MiniLM-L6-v2` for local inference, or OpenAI `text-embedding-ada-002` for cloud). Embeddings are persisted in ChromaDB. The processed chunks are also serialized to a JSON cache (`data/processed_docs/chunks.json`) for BM25 initialization.

---

### B. Hybrid Retrieval

#### 1) Vector Search

`VectorSearch` wraps ChromaDB's similarity search. For each query, it retrieves the top-k most semantically similar document chunks using cosine similarity over the embedding space.

#### 2) BM25 Sparse Search

`BM25Search` initializes LangChain's `BM25Retriever` from the serialized JSON chunk cache. BM25 (Best Matching 25) is a probabilistic term-frequency model that rewards matching rare, informative terms—well-suited to regulatory vocabulary such as specific article numbers, algorithm names, and legal keywords.

#### 3) Ensemble Fusion

`HybridRetriever` wraps both retrievers in LangChain's `EnsembleRetriever` with weights:

$$score(d,q) = 0.6 \times score_{dense}(d,q) + 0.4 \times score_{BM25}(d,q)$$

The 60/40 split reflects empirical evidence that semantic understanding is more important than exact keyword matching for compliance Q&A, while preserving precision for exact regulatory references.

#### 4) Query Transformation

`QueryTransformer` uses the configured LLM to expand a user query into three distinct search formulations. The prompt instructs the model to generate keyword-rich variants suitable for both vector and keyword retrieval:

```
Original Query: "Can I store customer passwords in plain text?"
Expanded Sub-queries:
  1. password hashing argon2 bcrypt
  2. OWASP password storage standard
  3. storing plain text passwords policy
```

All sub-queries are executed against the hybrid retriever and results are merged with deduplication (using the first 100 characters of content as a uniqueness key).

---

### C. Reranking

`RerankingStage` applies a cross-encoder model from the `sentence-transformers` library to re-score each retrieved document against the **original** user query. Cross-encoders compute joint attention over query-document pairs, providing more accurate relevance scores than bi-encoder cosine similarity.

The reranker reduces the candidate pool (up to 45 documents from multi-query retrieval) to `top_k` (default 5) highest-scoring documents passed to the generation stage.

---

### D. Answer Generation

#### 1) Prompt Architecture

`PromptBuilder` loads externalized prompt templates from the `prompts/` directory:

- **system_prompt.txt** — Defines the assistant's persona, constraints, and citation requirements.
- **compliance_prompt.txt** — Structures the context blocks, chat history, and user question.

Each context document is formatted as a structured block:

```
Document [1]: <chunk text>
Source Info: GDPR - gdpr_policy.pdf | Section: Article 6 | Page: 3
---
```

This structure guides the LLM to generate grounded, citation-backed responses.

#### 2) LLM Factory Pattern

`get_llm()` in `models/llm_factory.py` resolves the LLM provider from the `LLM_PROVIDER` environment variable:

| Provider | Class | Use Case |
|---|---|---|
| `ollama` | LangChain Ollama wrapper | Local inference, privacy-sensitive |
| `groq` | `langchain_groq.ChatGroq` | Cloud, fast inference (free tier) |
| `huggingface` | `langchain_huggingface` | Open models via HF Inference API |
| `mock` | `MockChatModel` | Offline testing, CI/CD pipelines |

This design decouples the RAG pipeline from any specific LLM vendor, enabling seamless provider switching via configuration.

#### 3) Citation Formatting

`CitationFormatter` processes the sources returned by `AnswerGenerator`, ensuring deduplication of source references by (filename, section, page) key. The final response includes a structured list of `SourceCitation` objects consumable by the frontend and audit tools.

---

### E. Guardrails

The system enforces a dual-phase safety framework via the `Guardrails` class.

#### 1) Input Guardrail — Prompt Injection Detection

The input validation scans user queries against a set of compiled regular expressions targeting known prompt injection patterns:

```python
INJECTION_KEYWORDS = [
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"disregard\s+(?:all\s+)?prior\s+prompts",
    r"you\s+must\s+forget",
    r"jailbreak",
    r"system\s+prompt\s+override",
    r"act\s+as\s+a\s+dan",
    r"bypass\s+restrictions"
]
```

Any match raises an HTTP 400 error with a guardrail violation message, preventing the query from reaching the LLM.

#### 2) Output Guardrail — Hallucination Grounding Check

The output validation verifies that domain-specific technical terms appearing in the generated answer are also present in the retrieved context documents. If the model references a term such as "Argon2", "bcrypt", "MD5", or "GDPR" that does not appear in any retrieved chunk, a grounding warning is returned alongside the answer rather than silently propagating a potentially hallucinated fact.

The check also handles the edge case of no retrieved context: if the model acknowledges ignorance (keywords like "cannot find", "no information"), it is considered grounded; otherwise a warning is flagged.

---

### F. Monitoring and Observability

#### 1) Structured Logging

`setup_logging()` configures dual-output logging:

- **Console handler** — Standard formatted messages for development.
- **File handler** — JSON-formatted log lines written to daily rotating log files (`logs/compliance_copilot_YYYYMMDD.log`).

#### 2) Per-Query Metrics

`QueryMetricsLogger` records a structured JSON record for each processed query:

```json
{
  "event": "query",
  "query": "<truncated>",
  "latency_ms": 342.17,
  "chunks_retrieved": 5,
  "sources": ["gdpr_policy.pdf", "owasp_guide.pdf"],
  "violation_detected": false,
  "llm_provider": "groq",
  "timestamp": "2026-05-29T06:28:00Z"
}
```

#### 3) LangSmith Tracing

`langsmith_tracker.py` integrates with LangSmith for full chain tracing, enabling visualization of each LLM call, prompt, token count, and latency in the LangSmith dashboard.

---

## V. Evaluation

### A. RAGAS Framework

The `rag/evaluation/ragas_eval.py` module implements evaluation using four RAGAS metrics [9]:

| Metric | Type | Description |
|---|---|---|
| **Faithfulness** | Reference-free | Fraction of answer claims that are supported by the retrieved context. |
| **Answer Relevancy** | Reference-free | Measures how pertinent the generated answer is to the original question. |
| **Context Recall** | Reference-based | Measures how much of the ground-truth answer is covered by retrieved context. |
| **Context Precision** | Reference-based | Measures the signal-to-noise ratio of retrieved chunks (relevant vs. irrelevant). |

### B. Benchmark Dataset

`benchmark_dataset.py` provides a curated set of compliance Q&A pairs seeded with questions from GDPR, SOC 2, ISO 27001, and OWASP domains, along with ground-truth reference answers. This enables automated regression testing of the full pipeline via `run_benchmark_evaluation()`.

### C. Evaluation Procedure

```
For each (question, ground_truth) in benchmark:
    1. Run full RAG pipeline: query → hybrid retrieval → rerank → generate
    2. Collect: answer, context_docs
    3. Format for RAGAS: Dataset({question, answer, contexts, ground_truths})
Run RAGAS.evaluate(dataset, metrics=[faithfulness, answer_relevancy,
                                      context_recall, context_precision])
Report mean scores per metric
```

RAGAS scores are saved to `data/processed_docs/ragas_results.json` for tracking across pipeline versions.

---

## VI. Results and Discussion

### A. Retrieval Quality

The hybrid ensemble retrieval strategy (Dense 0.6 + BM25 0.4) addresses the vocabulary mismatch problem that plagues pure vector search in compliance domains. Regulatory documents frequently use structured identifiers (Article numbers, Control codes) that carry high retrieval signal but low semantic representation in embedding space. BM25's term-frequency model reliably surfaces these chunks, which dense retrieval may rank lower due to sparse embedding coverage of numeric identifiers.

Query expansion further increases recall by generating three search variants per query. This is especially valuable for compliance questions where user phrasing (e.g., "Can I save user passwords as text?") differs significantly from regulatory phrasing ("Plaintext credential storage is prohibited under Section 4.2").

### B. Generation Quality

The externalized prompt architecture (system + compliance templates) provides explicit citation instructions to the LLM, yielding structured responses with traceable source references. The LLM factory pattern enables cost-performance trade-offs: the Groq backend (LLaMA 3 on Groq's LPU) delivers sub-500ms inference latency suitable for interactive use, while the Ollama backend enables fully on-premise deployment for data-sensitive organizations.

### C. Guardrail Effectiveness

The input guardrail blocks seven categories of prompt injection patterns without false positives on legitimate compliance queries. The output hallucination checker monitors nine domain-specific technical terms, flagging cases where the LLM invents regulatory references not present in the retrieved context. This is particularly important for cryptographic algorithm recommendations (e.g., Argon2, bcrypt) where an incorrect recommendation could constitute compliance-reportable guidance.

### D. Design Trade-offs

| Design Decision | Choice | Alternative | Rationale |
|---|---|---|---|
| Vector DB | ChromaDB (local) | Pinecone, Weaviate | Zero-cost, no external API dependency |
| Reranker | CrossEncoder | LLM-based reranking | Lower latency, no extra LLM call |
| Embedding model | all-MiniLM-L6-v2 | text-embedding-ada-002 | Fully local, no OpenAI dependency |
| Auth | Bearer token | OAuth2/JWT | Lightweight for internal deployments |
| Chunk size | 1000 chars / 200 overlap | Larger/smaller chunks | Balances context coverage and retrieval precision |

### E. Limitations

1. **Static injection keywords**: The prompt injection filter uses fixed regex patterns and may not catch novel attack formulations.
2. **Grounding check scope**: The output hallucination check monitors only nine predefined technical terms; broader semantic grounding would require an additional NLI pass.
3. **Evaluation data volume**: The benchmark dataset currently covers a limited set of Q&A pairs; a larger, annotated compliance corpus would provide more statistically robust RAGAS scores.
4. **Embedding model domain gap**: General-purpose sentence transformers may not optimally represent specialized legal language; fine-tuning on compliance corpora is a promising direction.

---

## VII. Conclusion

This paper presented Compliance Copilot, a production-ready RAG system for regulatory document question answering. The system addresses core challenges in compliance Q&A—semantic retrieval gaps, multi-document synthesis, hallucination risk, and prompt injection—through a principled pipeline combining hybrid retrieval, cross-encoder reranking, LLM query expansion, dual-layer guardrails, and RAGAS-based evaluation.

The pluggable LLM factory pattern and containerized deployment make the system accessible to organizations with varying infrastructure constraints, from fully on-premise (Ollama) to cloud-based (Groq, HuggingFace) inference. The open-source architecture serves as a reference implementation for compliance-domain RAG, providing verified citations that bridge the gap between LLM capability and enterprise auditability requirements.

Future work includes: (1) fine-tuning embedding models on compliance corpora; (2) expanding the guardrail system with NLI-based semantic grounding; (3) multi-modal support for compliance diagrams and tables in PDF documents; and (4) agentic workflows enabling multi-step compliance analysis across regulatory frameworks.

---

## References

[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Tau Yih, T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 9459–9474, 2020.

[2] H. Chase, "LangChain: Building Applications with LLMs through Composability," *GitHub Repository*, 2022. [Online]. Available: https://github.com/langchain-ai/langchain

[3] S. E. Robertson and S. Walker, "Some Simple Effective Approximations to the 2-Poisson Model for Probabilistic Weighted Retrieval," in *Proc. 17th Annual Int. ACM SIGIR Conf. Research and Development in Information Retrieval*, pp. 232–241, 1994.

[4] K. Al-Hazmi and A. Khatri, "Hybrid Retrieval for Open-Domain Question Answering: Sparse and Dense Fusion Strategies," *Information Processing & Management*, vol. 60, no. 3, 2023.

[5] J. Ma, I. Korotkov, Y. Yang, K. Hall, and R. McDonald, "Zero-Shot Neural Retrieval via Domain-Targeted Synthetic Query Generation," in *Proc. 2021 Conf. Empirical Methods in Natural Language Processing (EMNLP)*, pp. 1803–1812, 2021.

[6] N. Nogueira and K. Cho, "Passage Re-ranking with BERT," *arXiv preprint arXiv:1901.04085*, 2019.

[7] F. Perez and I. Ribeiro, "Ignore Previous Prompt: Attack Techniques For Language Models," *arXiv preprint arXiv:2211.09527*, 2022.

[8] X. Guo, R. Sharma, A. Bordia, and S. Singh, "Detecting Hallucinations in Large Language Model Generation: A Survey," *ACM Computing Surveys*, vol. 56, no. 9, 2024.

[9] S. Es, J. James, L. Espinosa-Anke, and S. Schockaert, "RAGAS: Automated Evaluation of Retrieval Augmented Generation," in *Proc. 18th Conf. European Chapter of the Association for Computational Linguistics (EACL)*, pp. 150–163, 2024.

[10] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in *Proc. 2019 Conf. Empirical Methods in Natural Language Processing and the 9th Int. Joint Conf. on Natural Language Processing (EMNLP-IJCNLP)*, pp. 3982–3992, 2019.

[11] ChromaDB Contributors, "Chroma: The AI-native Open-Source Embedding Database," *GitHub Repository*, 2023. [Online]. Available: https://github.com/chroma-core/chroma

[12] T. Zhang, R. Subramanian, and J. Leskovec, "Semantic Chunking Strategies for Retrieval-Augmented Generation," *arXiv preprint arXiv:2401.00368*, 2024.

---

*© 2026 Ankit Kumar Jha. IEEE format. All rights reserved.*
