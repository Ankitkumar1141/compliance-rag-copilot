"""
app.py — Streamlit Frontend for the Compliance Copilot.

Features:
  - Interactive chat with conversation memory
  - Expandable citation viewer per response
  - Document upload with live ingestion trigger
  - Analytics sidebar (latency, sources, violation flags)
  - Dark-themed, premium UI
"""

import os
import sys
import time
import requests
import streamlit as st

# ── Ensure project root is on sys.path ──
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv
load_dotenv()

# ── Config ──
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TOKEN   = os.getenv("API_BEARER_TOKEN")
if not API_TOKEN:
    raise RuntimeError("API_BEARER_TOKEN environment variable is not set.")
HEADERS     = {"Authorization": f"Bearer {API_TOKEN}"}

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Compliance Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS — Premium Dark Theme
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── App background ── */
    .stApp {
        background: linear-gradient(135deg, #0d0f1a 0%, #131629 50%, #0d0f1a 100%);
        color: #e2e8f0;
    }

    /* ── Header banner ── */
    .header-banner {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 50%, #1a3a6e 100%);
        border: 1px solid rgba(99,179,237,0.25);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .header-banner h1 {
        font-size: 2rem;
        font-weight: 700;
        color: #e2f0ff;
        margin: 0 0 6px 0;
    }
    .header-banner p {
        color: #93c5fd;
        font-size: 0.95rem;
        margin: 0;
    }

    /* ── Chat message bubbles ── */
    .user-bubble {
        background: linear-gradient(135deg, #1e40af, #2563eb);
        border-radius: 18px 18px 4px 18px;
        padding: 14px 18px;
        margin: 10px 0 10px 15%;
        color: #ffffff;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 4px 15px rgba(37,99,235,0.3);
        border: 1px solid rgba(147,197,253,0.2);
    }
    .assistant-bubble {
        background: linear-gradient(135deg, #1e293b, #1a2540);
        border-radius: 18px 18px 18px 4px;
        padding: 14px 18px;
        margin: 10px 15% 10px 0;
        color: #e2e8f0;
        font-size: 0.92rem;
        line-height: 1.7;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(99,179,237,0.15);
    }

    /* ── Violation badge ── */
    .violation-badge {
        background: linear-gradient(135deg, #7f1d1d, #991b1b);
        border: 1px solid #fca5a5;
        border-radius: 8px;
        padding: 8px 14px;
        color: #fecaca;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 10px;
        display: inline-block;
    }
    .compliant-badge {
        background: linear-gradient(135deg, #14532d, #166534);
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 8px 14px;
        color: #bbf7d0;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 10px;
        display: inline-block;
    }

    /* ── Source chip ── */
    .source-chip {
        display: inline-block;
        background: rgba(37,99,235,0.15);
        border: 1px solid rgba(99,179,237,0.3);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.78rem;
        color: #93c5fd;
        margin: 3px;
    }

    /* ── Metric card ── */
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #1a2540);
        border: 1px solid rgba(99,179,237,0.15);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #60a5fa;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 2px;
    }

    /* ── Input box ── */
    .stTextArea textarea {
        background: #1e293b !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(99,179,237,0.3) !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96,165,250,0.2) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1e40af, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
        box-shadow: 0 4px 15px rgba(37,99,235,0.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #131a2e 100%) !important;
        border-right: 1px solid rgba(99,179,237,0.1) !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: rgba(30,41,59,0.8) !important;
        border-radius: 8px !important;
        color: #93c5fd !important;
    }

    /* ── Divider ── */
    hr { border-color: rgba(99,179,237,0.1) !important; }

    /* ── Quick question pills ── */
    .quick-q {
        background: rgba(30,58,95,0.5);
        border: 1px solid rgba(99,179,237,0.2);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.82rem;
        color: #93c5fd;
        cursor: pointer;
        display: inline-block;
        margin: 4px;
        transition: all 0.2s;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Session State Initialisation
# ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # list of {"role", "content", "sources", "latency_ms", "warning"}
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "total_violations" not in st.session_state:
    st.session_state.total_violations = 0
if "avg_latency" not in st.session_state:
    st.session_state.avg_latency = 0.0
if "latencies" not in st.session_state:
    st.session_state.latencies = []

# ─────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────

def call_chat_api(query: str, history_str: str, top_k: int = 5):
    """Call the FastAPI /chat endpoint and return result dict."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/chat",
            json={"query": query, "chat_history": history_str, "top_k": top_k},
            headers=HEADERS,
            timeout=120,
        )
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"API Error {resp.status_code}: {resp.json().get('detail', resp.text)}"
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to the backend. Make sure the FastAPI server is running on port 8000."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def call_upload_api(file_bytes, filename):
    """Call the FastAPI /upload endpoint."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/upload",
            files={"file": (filename, file_bytes)},
            headers=HEADERS,
            timeout=300,
        )
        if resp.status_code == 200:
            return resp.json(), None
        else:
            return None, f"Upload Error {resp.status_code}: {resp.json().get('detail', resp.text)}"
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot connect to the backend."
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def check_backend_health():
    """Check backend health status."""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def render_badge(answer_text: str):
    if "[POLICY VIOLATION" in answer_text.upper():
        st.markdown('<span class="violation-badge">🚨 POLICY VIOLATION DETECTED</span>', unsafe_allow_html=True)
    elif "[COMPLIANT]" in answer_text.upper() or "[ERROR]" not in answer_text.upper():
        st.markdown('<span class="compliant-badge">✅ ANALYSIS COMPLETE</span>', unsafe_allow_html=True)


def build_history_string():
    """Build a short history string from last 3 exchanges."""
    history_parts = []
    for msg in st.session_state.messages[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_parts.append(f"{role}: {msg['content'][:200]}")
    return "\n".join(history_parts)


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛡️ Compliance Copilot")
    st.markdown("---")

    # Backend health
    health = check_backend_health()
    if health:
        st.markdown(f"**Backend:** 🟢 Online")
        st.markdown(f"**LLM:** `{health.get('llm_provider', '?')}`")
        st.markdown(f"**Embeddings:** `{health.get('embedding_provider', '?')}`")
        db_ready = health.get("vector_db_ready", False)
        st.markdown(f"**Vector DB:** {'🟢 Ready' if db_ready else '🔴 Not ingested'}")
    else:
        st.markdown("**Backend:** 🔴 Offline")
        st.info("Start the API:\n```\npython -m app.backend.main\n```")

    st.markdown("---")

    # ── Analytics ──
    st.markdown("### 📊 Session Analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.total_queries}</div>
            <div class="metric-label">Queries</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{st.session_state.total_violations}</div>
            <div class="metric-label">Violations</div>
        </div>""", unsafe_allow_html=True)

    avg_lat = round(sum(st.session_state.latencies) / len(st.session_state.latencies), 0) if st.session_state.latencies else 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{avg_lat}ms</div>
        <div class="metric-label">Avg Latency</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Settings ──
    st.markdown("### ⚙️ Retrieval Settings")
    top_k = st.slider("Documents to retrieve (top-k)", min_value=1, max_value=15, value=5, step=1)

    st.markdown("---")

    # ── Document Upload ──
    st.markdown("### 📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload compliance doc (PDF, DOCX, MD, TXT)",
        type=["pdf", "docx", "md", "txt"],
        key="doc_uploader",
    )
    if uploaded_file:
        if st.button("🚀 Ingest Document"):
            with st.spinner(f"Ingesting `{uploaded_file.name}`..."):
                result, err = call_upload_api(uploaded_file.getvalue(), uploaded_file.name)
            if err:
                st.error(err)
            else:
                st.success(f"✅ Ingested! Created **{result['chunks_created']}** chunks.")

    st.markdown("---")

    # ── Clear History ──
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.total_queries = 0
        st.session_state.total_violations = 0
        st.session_state.latencies = []
        st.rerun()

# ─────────────────────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="header-banner">
    <h1>🛡️ Compliance Copilot</h1>
    <p>Ask questions about GDPR, SOC2, ISO27001, OWASP, and your internal engineering policies — with cited answers.</p>
</div>
""", unsafe_allow_html=True)

# Quick example questions
st.markdown("**💡 Try these questions:**")
quick_questions = [
    "Can I store customer passwords in plain text?",
    "What is the legal basis for processing personal data under GDPR?",
    "Is MFA required for production access?",
    "What hashing algorithms are allowed for passwords?",
    "Can passwords be sent over HTTP?",
]
q_cols = st.columns(len(quick_questions))
for i, qq in enumerate(quick_questions):
    if q_cols[i].button(qq[:35] + "…" if len(qq) > 35 else qq, key=f"quick_{i}"):
        st.session_state["prefill_query"] = qq

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# Chat History Rendering
# ─────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="assistant-bubble">', unsafe_allow_html=True)
            render_badge(msg["content"])
            st.markdown(msg["content"])

            # Sources expander
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📚 View {len(sources)} Source Citation(s)", expanded=False):
                    for i, src in enumerate(sources):
                        st.markdown(
                            f"**[{i+1}]** `{src.get('category','?')}` — "
                            f"**{src.get('source','?')}** | "
                            f"Section: `{src.get('section','?')}` | "
                            f"Page: `{src.get('page','?')}`"
                        )

            # Guardrail warning
            warning = msg.get("warning")
            if warning:
                st.warning(f"⚠️ {warning}")

            # Latency
            lat = msg.get("latency_ms", 0)
            st.caption(f"⏱ Response time: {lat:.0f}ms")
            st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Query Input
# ─────────────────────────────────────────────────────────────
st.markdown("---")

prefill = st.session_state.pop("prefill_query", "")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_area(
        "Ask a compliance question:",
        value=prefill,
        placeholder="e.g. Can I store customer passwords in plain text?",
        height=100,
        key="user_query_input",
        label_visibility="visible",
    )
    submit = st.form_submit_button("🔍 Ask Compliance Copilot", use_container_width=True)

if submit and user_input.strip():
    query = user_input.strip()

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.total_queries += 1

    # Build history context
    history_str = build_history_string()

    with st.spinner("🔍 Searching compliance documents and generating answer..."):
        result, err = call_chat_api(query, history_str, top_k=top_k)

    if err:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Error:** {err}",
            "sources": [],
            "latency_ms": 0,
            "warning": None,
        })
    else:
        answer = result.get("answer", "No answer returned.")
        sources = result.get("sources", [])
        latency = result.get("latency_ms", 0)
        warning = result.get("guardrail_warning")

        if "[POLICY VIOLATION" in answer.upper():
            st.session_state.total_violations += 1

        st.session_state.latencies.append(latency)
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "latency_ms": latency,
            "warning": warning,
        })

    st.rerun()
