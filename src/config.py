import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Backend selection: "gemini" (free) or "azure"
    BACKEND = os.getenv("BACKEND", "gemini")

    # ── Gemini backend ──
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # ── Azure backend ──
    PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
    MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT", "gpt-4o-deploy")
    AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
    AZURE_RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP")
    AZURE_PROJECT_NAME = os.getenv("AZURE_PROJECT_NAME")

    @classmethod
    def validate(cls):
        """Validate that required env vars are set for the chosen backend."""
        if cls.BACKEND == "azure":
            required = ["PROJECT_ENDPOINT", "MODEL_DEPLOYMENT"]
        elif cls.BACKEND == "gemini":
            required = ["GEMINI_API_KEY"]
        else:
            raise ValueError(
                f"Unknown BACKEND: '{cls.BACKEND}'. Use 'azure' or 'gemini'."
            )

        missing = [f for f in required if not getattr(cls, f)]
        if missing:
            raise ValueError(
                f"Missing env vars for {cls.BACKEND}: {', '.join(missing)}"
            )
