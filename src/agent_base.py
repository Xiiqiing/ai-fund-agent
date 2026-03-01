"""
Base agent interface for the AI Fund Operations Assistant.
All backends (Azure, Gemini, etc.) implement this interface.
"""

import json
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class defining the agent interface."""

    @abstractmethod
    def setup(self, knowledge_dir: str = "data/knowledge_base"):
        """Initialize the agent with knowledge base documents."""

    @abstractmethod
    def ask(self, question: str) -> str:
        """Send a question to the agent and return the response."""

    @abstractmethod
    def cleanup(self):
        """Clean up resources."""

    def extract(self, document_text: str) -> dict:
        """Extract structured data from a document.

        This method is shared across all backends — it sends an extraction
        prompt to self.ask() and parses the JSON response.
        """
        prompt = (
            "Extract key investment terms from the following document. "
            "Return ONLY valid JSON with these fields: "
            "fund_name, project_name, location, technology, capacity, "
            "total_investment, target_irr, investment_period, cod_date, "
            "ppa_status, esg_rating, key_risks. "
            "Set missing fields to null.\n\n"
            f"Document:\n{document_text}"
        )
        response = self.ask(prompt)

        # Try to parse JSON from response
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"raw_response": response, "parse_error": True}
