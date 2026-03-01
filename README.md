# AI Fund Operations Agent

An AI-powered assistant. Support both Google Gemini and Azure AI Foundry.

## Features

| Feature | Description |
|---------|-------------|
| **Knowledge Q&A (RAG)** | Vector search over sample energy reports, returns sourced answers |
| **Document Extraction** | Parses investment memos into structured JSON |
| **Pluggable Backend** | Switch between Gemini and Azure with one env var |
| **Containerized** | Dockerfile for consistent deployment across environments |
| **CI/CD Pipeline** | GitHub Actions with AI Validation |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Streamlit Web UI (app.py)                          │
│    ├── Backend selector (sidebar)                   │
│    ├── Chat interface                               │
│    └── JSON extraction display                      │
├─────────────────────────────────────────────────────┤
│  create_agent() — Backend Factory                   │
│    ├── GeminiAgent   (default)                │
│    │     ├── Gemini 2.5 Flash                 │
│    │     ├── Gemini Embedding (vectorization)        │
│    │     └── numpy _VectorStore (cosine similarity)  │
│    │                                                │
│    └── AzureAgent    (requires subscription)        │
│          ├── GPT-4o via Azure Agent Service          │
│          └── Azure File Search (managed RAG)         │
├─────────────────────────────────────────────────────┤
│  data/knowledge_base/   ← PDF, MD, TXT documents   │
└─────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and setup
git clone https://github.com/<your-username>/ai-fund-agent.git
cd ai-fund-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure (get free key at https://aistudio.google.com/apikey)
cp .env.example .env
# Edit .env: set BACKEND=gemini, GEMINI_API_KEY=your-key

# Run
streamlit run app.py
```

## Docker

The Dockerfile packages the web application, RAG pipeline, and knowledge base into a container. Docker wraps the application layer.

```bash
# Build
docker build -t ai-fund-agent:latest .

# Run with Gemini backend
docker run -p 8501:8501 \
  -e BACKEND=gemini \
  -e GEMINI_API_KEY=your-key \
  ai-fund-agent:latest
```

## Project Structure

```
├── src/
│   ├── agent.py              # Backend factory
│   ├── agent_base.py         # Abstract base class
│   ├── agent_azure.py        # Azure AI Foundry backend
│   ├── agent_gemini.py       # Gemini + numpy vector search
│   ├── config.py             # Configuration management
│   └── prompts/
│       └── system_prompt.txt
├── data/
│   ├── knowledge_base/       # RAG documents (PDF, MD, TXT)
│   └── sample_docs/          # Test documents
├── tests/
│   └── test_agent.py         # Unit + integration tests
├── scripts/
│   └── smoke_test.sh         # Health check script
├── .github/workflows/
│   └── ci-cd.yml             # CI/CD pipeline
├── Dockerfile
├── deploy.py                 # Automated deployment
└── requirements.txt
```

## Backend Configuration

```bash
# Gemini (free, default)
BACKEND=gemini
GEMINI_API_KEY=your-key

# Azure AI Foundry
BACKEND=azure
PROJECT_ENDPOINT=https://...
MODEL_DEPLOYMENT=gpt-4o-deploy
```

## Testing

```bash
# Unit tests (no credentials needed)
python -m pytest tests/ -v -k "not Integration"

# All tests (requires configured backend)
python -m pytest tests/ -v
```

## CI/CD Pipeline

5-stage production pipeline on push to `main`:

1. **Lint & Test** — ruff + pytest
2. **Build & Push** — Docker image → ACR, Trivy vulnerability scan
3. **Deploy Staging** — Container Apps + smoke test
4. **AI Validation** — Response quality, extraction accuracy, latency check
5. **Promote Production** — Traffic routing + health check

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini / Azure models |
| RAG | numpy cosine similarity / Azure File Search |
| Web UI | Streamlit |
| Container | Docker |
| CI/CD | GitHub Actions |
| Testing | pytest + ruff |
