"""
Automated tests for AI Fund Operations Agent.
Tests are designed to verify:
1. Agent extract returns valid structured JSON (shared logic)
2. Configuration validation works for all backends
3. Integration tests run against configured backend
"""
import json
import os
import pytest
from unittest.mock import patch, MagicMock

from src.agent_base import BaseAgent


# ── Testable agent stub (no real backend needed) ──


class _MockAgent(BaseAgent):
    """Concrete subclass for testing shared BaseAgent methods."""

    def setup(self, knowledge_dir="data/knowledge_base"):
        pass

    def ask(self, question):
        return ""

    def cleanup(self):
        pass


# --- Unit Tests (no Azure or Gemini connection needed) ---


class TestExtractJsonParsing:
    """Test JSON extraction logic (shared across all backends)."""

    def test_clean_json_response(self):
        """Valid JSON is parsed correctly."""
        agent = _MockAgent()

        mock_response = json.dumps({
            "fund_name": "Energy Transition Fund I",
            "project_name": "Nordic Wind Farm Alpha",
            "location": "Denmark, North Sea",
            "technology": "Offshore Wind",
            "capacity": "800 MW",
            "total_investment": "EUR 2.4 billion",
            "target_irr": "8-10%",
            "investment_period": "25 years",
            "cod_date": "Q4 2027",
            "ppa_status": "60% contracted",
            "esg_rating": "A+ (GRESB)",
            "key_risks": ["Permitting delays", "Supply chain", "Grid connection"],
        })

        with patch.object(agent, "ask", return_value=mock_response):
            result = agent.extract("test document text")

        assert isinstance(result, dict)
        assert result["fund_name"] == "Energy Transition Fund I"
        assert result["capacity"] == "800 MW"
        assert result["target_irr"] == "8-10%"
        assert "parse_error" not in result

    def test_markdown_wrapped_json(self):
        """JSON wrapped in markdown code blocks is handled."""
        agent = _MockAgent()

        mock_response = (
            '```json\n{"fund_name": "Test Fund", "capacity": "500 MW"}\n```'
        )

        with patch.object(agent, "ask", return_value=mock_response):
            result = agent.extract("test")

        assert result["fund_name"] == "Test Fund"
        assert "parse_error" not in result

    def test_invalid_json_returns_raw(self):
        """Invalid JSON returns raw response with error flag."""
        agent = _MockAgent()

        with patch.object(agent, "ask", return_value="This is not JSON at all"):
            result = agent.extract("test")

        assert result["parse_error"] is True
        assert "raw_response" in result


class TestConfigValidation:
    """Test configuration validation."""

    def test_missing_azure_env_raises_error(self):
        from src.config import Config

        with patch.dict(os.environ, {"BACKEND": "azure"}, clear=True):
            Config.BACKEND = "azure"
            Config.PROJECT_ENDPOINT = None
            Config.MODEL_DEPLOYMENT = None
            with pytest.raises(ValueError, match="Missing env vars"):
                Config.validate()

    def test_missing_gemini_env_raises_error(self):
        from src.config import Config

        with patch.dict(os.environ, {"BACKEND": "gemini"}, clear=True):
            Config.BACKEND = "gemini"
            Config.GEMINI_API_KEY = None
            with pytest.raises(ValueError, match="Missing env vars"):
                Config.validate()

    def test_invalid_backend_raises_error(self):
        from src.config import Config

        Config.BACKEND = "invalid"
        with pytest.raises(ValueError, match="Unknown BACKEND"):
            Config.validate()


class TestAgentFactory:
    """Test the agent factory function."""

    def test_factory_raises_on_unknown_backend(self):
        from src.config import Config

        original = Config.BACKEND
        Config.BACKEND = "unknown"
        try:
            from src.agent import create_agent
            with pytest.raises(ValueError, match="Unknown backend"):
                create_agent()
        finally:
            Config.BACKEND = original


# --- Integration Tests (require configured backend) ---


@pytest.mark.skipif(
    not (os.getenv("PROJECT_ENDPOINT") or os.getenv("GEMINI_API_KEY")),
    reason="No backend credentials configured — skipping integration tests",
)
class TestAgentIntegration:
    """Integration tests that connect to the configured backend."""

    @pytest.fixture(scope="class")
    def agent(self):
        from src.agent import create_agent

        a = create_agent()
        a.setup(knowledge_dir="data/knowledge_base")
        yield a
        a.cleanup()

    def test_qa_returns_nonempty_response(self, agent):
        response = agent.ask("What are the main types of renewable energy?")
        assert len(response) > 20
        assert isinstance(response, str)

    def test_extraction_returns_valid_structure(self, agent):
        sample_doc = open("data/sample_docs/investment_memo_sample.md").read()
        result = agent.extract(sample_doc)
        assert isinstance(result, dict)
        assert "fund_name" in result or "raw_response" in result

    def test_unknown_question_handled(self, agent):
        response = agent.ask(
            "What is the exact revenue of project XYZ-999 in Q3 2024?"
        )
        assert isinstance(response, str)
        assert len(response) > 0
