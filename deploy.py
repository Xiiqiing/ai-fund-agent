"""
Automated deployment script for AI Fund Operations Assistant.
Used by GitHub Actions CI/CD pipeline.

Usage:
    python deploy.py                  # Deploy with default settings
    python deploy.py --update-prompt  # Update system prompt only
"""
import argparse
import sys
from pathlib import Path
from src.agent import create_agent
from src.config import Config


def deploy(update_prompt_only: bool = False):
    """Deploy or update the AI Agent."""
    print("=" * 50)
    print("AI Fund Agent — Deployment")
    print("=" * 50)

    Config.validate()
    print("Config validated")
    print(f"   Backend: {Config.BACKEND}")

    agent = create_agent()

    try:
        # Set up agent with knowledge base
        agent.setup(knowledge_dir="data/knowledge_base")

        # Run a smoke test
        print("\nRunning smoke test...")
        response = agent.ask("What types of renewable energy exist?")
        if len(response) > 10:
            print(f"✅ Smoke test passed ({len(response)} chars)")
        else:
            print("❌ Smoke test failed: response too short")
            sys.exit(1)

        # Test extraction
        sample_path = Path("data/sample_docs/investment_memo_sample.md")
        if sample_path.exists():
            result = agent.extract(sample_path.read_text())
            if "parse_error" not in result:
                print("✅ Extraction test passed")
            else:
                print("⚠️  Extraction returned raw text (non-blocking)")

        print("\n" + "=" * 50)
        print("✅ Deployment complete!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        agent.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy AI Fund Agent")
    parser.add_argument(
        "--update-prompt",
        action="store_true",
        help="Only update the system prompt",
    )
    args = parser.parse_args()
    deploy(update_prompt_only=args.update_prompt)
