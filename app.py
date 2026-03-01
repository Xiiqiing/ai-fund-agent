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
    .stApp { background-color: #0e1117; }
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
        background: #1a1a2e;
        border: 1px solid #333;
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

    # ── About ──
    st.header("About")
    st.markdown("""
    **Capabilities:**
    - Q&A over renewable energy reports
    - Extract structured data from investment memos

    **Try asking:**
    - *"What is the LCOE for offshore wind?"*
    - *"Extract key terms from this memo: ..."*
    """)

    # Quick-fill extraction button
    if st.button("Load sample memo"):
        try:
            with open("data/sample_docs/investment_memo_sample.md") as f:
                sample = f.read()
            st.session_state["prefill"] = (
                f"Extract key investment terms from:\n\n{sample}"
            )
        except FileNotFoundError:
            st.warning("Sample file not found")


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
prompt = st.chat_input("Ask about renewable energy or paste a document...") or prefill

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
