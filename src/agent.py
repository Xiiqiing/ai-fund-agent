"""
AI Fund Operations Assistant — Backend Factory

Supports multiple backends:
  - "gemini" → Google Gemini API + numpy vector search (default)
  - "azure"  → Azure AI Foundry Agent Service (requires subscription)

Set BACKEND env var to switch. Default: "gemini"
"""
from src.config import Config


def create_agent():
    """Create an agent instance based on the configured backend.

    Returns:
        BaseAgent: An agent with .setup(), .ask(), .extract(), .cleanup()
    """
    backend = Config.BACKEND

    if backend == "azure":
        from src.agent_azure import AzureAgent

        return AzureAgent()

    elif backend == "gemini":
        from src.agent_gemini import GeminiAgent

        return GeminiAgent()

    else:
        raise ValueError(
            f"Unknown backend: '{backend}'. Use 'azure' or 'gemini'."
        )
