"""
Azure AI Foundry backend for the AI Fund Operations Assistant.
Uses Azure Agent Service with File Search (RAG) and GPT-4o.

Requires:
  - Azure subscription with AI Foundry project
  - Environment variables: PROJECT_ENDPOINT, MODEL_DEPLOYMENT
"""
from pathlib import Path
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import (
    FileSearchTool,
    FilePurpose,
    MessageRole,
    ListSortOrder,
)
from azure.identity import DefaultAzureCredential
from src.agent_base import BaseAgent
from src.config import Config


class AzureAgent(BaseAgent):
    """Fund Operations Agent using Azure AI Foundry Agent Service."""

    def __init__(self):
        Config.validate()
        self.client = AIProjectClient(
            endpoint=Config.PROJECT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        self.agent = None
        self.vector_store = None

    def setup(self, knowledge_dir: str = "data/knowledge_base"):
        """Initialize the agent with knowledge base documents."""
        # 1. Upload knowledge base files
        uploaded_files = self._upload_files(knowledge_dir)

        # 2. Create vector store for RAG
        if uploaded_files:
            self.vector_store = self.client.agents.create_vector_store_and_poll(
                file_ids=[f.id for f in uploaded_files],
                name="fund-knowledge-base",
            )
            print(f"Vector store created: {self.vector_store.id}")

        # 3. Load system prompt
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
        system_prompt = prompt_path.read_text(encoding="utf-8")

        # 4. Create agent with file search tool
        tools = []
        tool_resources = {}
        if self.vector_store:
            tools.append(FileSearchTool())
            tool_resources = {
                "file_search": {"vector_store_ids": [self.vector_store.id]}
            }

        self.agent = self.client.agents.create_agent(
            model=Config.MODEL_DEPLOYMENT,
            name="AI Fund Assistant",
            instructions=system_prompt,
            tools=tools,
            tool_resources=tool_resources,
        )
        print(f"Agent created: {self.agent.id}")

    def _upload_files(self, directory: str):
        """Upload all PDF/MD files in the given directory."""
        uploaded = []
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Directory {directory} not found, skipping file upload.")
            return uploaded

        for file_path in dir_path.glob("*"):
            if file_path.suffix.lower() in (".pdf", ".md", ".txt", ".docx"):
                with open(file_path, "rb") as f:
                    uploaded_file = self.client.agents.upload_file_and_poll(
                        file=f,
                        purpose=FilePurpose.AGENTS,
                    )
                    uploaded.append(uploaded_file)
                    print(f"  Uploaded: {file_path.name}")
        return uploaded

    def ask(self, question: str) -> str:
        """Send a question to the agent and return the response."""
        if not self.agent:
            raise RuntimeError("Agent not set up. Call setup() first.")

        # Create a thread
        thread = self.client.agents.create_thread()

        # Add user message
        self.client.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content=question,
        )

        # Run the agent
        run = self.client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=self.agent.id,
        )

        if run.status == "failed":
            raise RuntimeError(f"Agent run failed: {run.last_error}")

        # Get the response
        messages = self.client.agents.list_messages(
            thread_id=thread.id,
            order=ListSortOrder.DESCENDING,
        )

        # Return the last assistant message
        for msg in messages.data:
            if msg.role == MessageRole.AGENT:
                return msg.content[0].text.value
        return ""

    def cleanup(self):
        """Clean up resources."""
        if self.agent:
            self.client.agents.delete_agent(self.agent.id)
            print(f"Agent deleted: {self.agent.id}")
        if self.vector_store:
            self.client.agents.delete_vector_store(self.vector_store.id)
            print(f"Vector store deleted: {self.vector_store.id}")
