"""
AI Fund Operations Assistant — Web Interface
A Streamlit app that provides a chat UI for the AI Agent.
Supports switching between Gemini (free) and Azure backends from the sidebar.
"""
import os
import json
import streamlit as st
from src.config import Config

# ── Page Config ──
st.set_page_config(
    page_title="AI Fund Assistant",
    page_icon="🌊",
    layout="centered",
)

# ── Custom Styling ──
st.markdown("""
<style>
    /* Use Streamlit's native theme for the main app background */
    .main-header {
        background: linear-gradient(135deg, #006B3F 0%, #00A86B 50%, #2196F3 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .feature-badge {
        display: inline-block;
        background: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown(
    '<div class="main-header">🌊 AI Fund Assistant</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">AI-powered Q&A and document extraction for renewable energy fund operations<br>'
    '<span class="feature-badge">RAG Knowledge Base</span>'
    '<span class="feature-badge">Document Extraction</span>'
    '<span class="feature-badge">Pluggable Backend</span>'
    "</div>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div style="text-align:center; margin: -1rem 0 1.5rem 0; font-size: 0.9rem;">'
    'Visit new version: '
    '<a href="https://github.com/Xiiqiing/Dokumentassistent" target="_blank" rel="noopener" '
    'style="text-decoration:none; display:inline-flex; align-items:center; gap:0.35rem; vertical-align:middle;">'
    '<svg height="16" width="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
    '0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
    '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
    '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 '
    '2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 '
    '3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 '
    '8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
    '<span>github.com/Xiiqiing/Dokumentassistent</span></a>'
    '</div>',
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════
# Sidebar — Backend Configuration
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.header("Backend")

    default_backend = os.getenv("BACKEND", "gemini")
    backend = st.radio(
        "Select AI backend",
        ["gemini", "azure"],
        index=0 if default_backend == "gemini" else 1,
        format_func=lambda x: "Gemini (Free)" if x == "gemini" else "Azure AI Foundry",
        help="Gemini is free. Azure requires a subscription.",
    )

    st.divider()

    # ── Gemini Config ──
    if backend == "gemini":
        st.markdown("**Gemini Configuration**")

        env_key = os.getenv("GEMINI_API_KEY", "")

        if env_key:
            st.success("API Key configured")
            # Allow override but don't show default
            override = st.text_input(
                "Override API Key (optional)",
                value="",
                type="password",
                placeholder="Leave empty to use configured key",
            )
            gemini_key = override if override else env_key
        else:
            st.caption("Get a free key at [aistudio.google.com](https://aistudio.google.com/apikey)")
            gemini_key = st.text_input(
                "Gemini API Key",
                value="",
                type="password",
                placeholder="AIzaSy...",
            )

        # Store config
        config_ready = bool(gemini_key)
        if not config_ready:
            st.warning("Enter your Gemini API Key to start")

        # Apply to Config
        Config.BACKEND = "gemini"
        Config.GEMINI_API_KEY = gemini_key

    # ── Azure Config ──
    else:
        st.markdown("**Azure AI Foundry Configuration**")
        st.caption("Enter your Azure AI Foundry project details")

        az_endpoint = st.text_input(
            "Project Endpoint",
            value=os.getenv("PROJECT_ENDPOINT", ""),
            placeholder="https://xxx.services.ai.azure.com/api",
            help="Found in AI Foundry → Settings → Overview",
        )
        az_model = st.text_input(
            "Model Deployment",
            value=os.getenv("MODEL_DEPLOYMENT", "gpt-4o-deploy"),
            help="The name you gave your GPT-4o deployment",
        )

        with st.expander("Service Principal Credentials", expanded=not bool(os.getenv("AZURE_CLIENT_ID"))):
            st.caption("Required for authentication. [How to create →](https://learn.microsoft.com/en-us/entra/identity-platform/howto-create-service-principal-portal)")
            az_client_id = st.text_input(
                "Client ID (appId)",
                value=os.getenv("AZURE_CLIENT_ID", ""),
                type="password",
            )
            az_client_secret = st.text_input(
                "Client Secret (password)",
                value=os.getenv("AZURE_CLIENT_SECRET", ""),
                type="password",
            )
            az_tenant_id = st.text_input(
                "Tenant ID",
                value=os.getenv("AZURE_TENANT_ID", ""),
                type="password",
            )

        # Store config
        config_ready = bool(az_endpoint and az_model)
        if not config_ready:
            st.warning("Fill in your Azure project details to start")
        else:
            st.info(
                "Azure mode will auto-upload files from `data/knowledge_base/` "
                "to Azure File Search on first connection. "
                "An active Azure subscription is required."
            )

        # Apply to Config and env vars (for DefaultAzureCredential)
        Config.BACKEND = "azure"
        Config.PROJECT_ENDPOINT = az_endpoint
        Config.MODEL_DEPLOYMENT = az_model
        if az_client_id:
            os.environ["AZURE_CLIENT_ID"] = az_client_id
        if az_client_secret:
            os.environ["AZURE_CLIENT_SECRET"] = az_client_secret
        if az_tenant_id:
            os.environ["AZURE_TENANT_ID"] = az_tenant_id

    st.divider()

    # Show loaded knowledge base files (cached for performance)
    from pathlib import Path

    @st.cache_data(ttl=60)
    def get_kb_files(kb_path, sample_path):
        kb_files = []
        if Path(kb_path).exists():
            kb_files = sorted(Path(kb_path).glob("*"))
            kb_files = [f.name for f in kb_files if f.suffix.lower() in (".md", ".txt", ".pdf")]
        
        sample_files = []
        if Path(sample_path).exists():
            sample_files = sorted(Path(sample_path).glob("*"))
            sample_files = [f.name for f in sample_files]
            
        return kb_files, sample_files

    kb_files_list, sample_files_list = get_kb_files("data/knowledge_base", "data/sample_docs")

    if kb_files_list:
        st.caption(f"RAG indexed ({len(kb_files_list)} files):")
        for name in kb_files_list:
            st.markdown(f"- `{name}`")
    else:
        st.caption("No documents in `data/knowledge_base/`")

    if sample_files_list:
        st.caption("Sample documents:")
        for name in sample_files_list:
            st.markdown(f"- `{name}`")

    st.divider()

    # Quick-fill extraction button
    if st.button("Load sample memo for extraction"):
        try:
            with open("data/sample_docs/investment_memo_sample.md") as f:
                sample = f.read()
            st.session_state["prefill"] = (
                f"Extract key investment terms from:\n\n{sample}"
            )
        except FileNotFoundError:
            st.warning("Sample file not found")

    st.divider()

    # ── About ──
    st.header("About")
    st.markdown("""
    **Try asking:**
    - *"What is the LCOE for offshore wind?"*
    - *"What are the key risks for offshore wind?"*
    - *"Extract key terms from this memo: ..."*
    """)


# ══════════════════════════════════════════════════════
# Agent Initialization
# ══════════════════════════════════════════════════════

def _config_key():
    """Generate a unique key for current config to manage caching."""
    if Config.BACKEND == "gemini":
        return f"gemini:{Config.GEMINI_API_KEY or ''}"
    else:
        return f"azure:{Config.PROJECT_ENDPOINT or ''}:{Config.MODEL_DEPLOYMENT or ''}"


@st.cache_resource(show_spinner="Connecting to AI Agent...")
def get_agent(_config_key: str):
    """Create and cache agent. Cache invalidated when config changes."""
    from src.agent import create_agent
    agent = create_agent()
    agent.setup(knowledge_dir="data/knowledge_base")
    return agent


if not config_ready:
    st.info("Configure your AI backend in the sidebar to get started.")
    st.stop()

try:
    agent = get_agent(_config_key())
except Exception as e:
    st.error(f"Could not initialize agent: {e}")
    st.stop()


# ══════════════════════════════════════════════════════
# Chat Interface
# ══════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm the AI Fund Assistant. "
                "Ask me about renewable energy projects, or paste an "
                "investment memo for data extraction. 🌊"
            ),
        }
    ]

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
prefill = st.session_state.pop("prefill", None)
prompt = st.chat_input("Ask about renewable energy or paste a document (text)...") or prefill

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            is_extraction = any(
                kw in prompt.lower()
                for kw in ["extract", "parse", "analyze", "key terms"]
            )

            if is_extraction:
                result = agent.extract(prompt)
                if "parse_error" not in result:
                    response = (
                        f"**📄 Extracted Data:**\n"
                        f"```json\n{json.dumps(result, indent=2)}\n```"
                    )
                else:
                    response = result.get("raw_response", "Could not extract data.")
            else:
                response = agent.ask(prompt)

        st.markdown(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )
