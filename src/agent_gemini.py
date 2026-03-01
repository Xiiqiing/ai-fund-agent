"""
Gemini backend for the AI Fund Operations Assistant.

Requires:
  - GEMINI_API_KEY (get free at https://aistudio.google.com/apikey)

Free tier limits:
  - 15 requests/minute, 1M tokens/day — plenty for a demo

Dependencies: google-genai, numpy, pypdf (for PDFs)
"""
import time
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from src.agent_base import BaseAgent
from src.config import Config


class _VectorStore:
    """Lightweight in-memory vector store using numpy cosine similarity."""

    def __init__(self):
        self.documents: list[str] = []
        self.metadatas: list[dict] = []
        self.embeddings: np.ndarray | None = None

    def add(self, documents: list[str], metadatas: list[dict], embeddings: list[list[float]]):
        """Add documents with pre-computed embeddings."""
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        new_emb = np.array(embeddings, dtype=np.float32)
        if self.embeddings is None:
            self.embeddings = new_emb
        else:
            self.embeddings = np.vstack([self.embeddings, new_emb])

    def query(self, query_embedding: list[float], n_results: int = 5) -> list[tuple[str, dict, float]]:
        """Return top-n most similar documents by cosine similarity."""
        if self.embeddings is None or len(self.documents) == 0:
            return []

        q = np.array(query_embedding, dtype=np.float32)
        # Cosine similarity
        norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(q)
        norms = np.where(norms == 0, 1e-10, norms)
        similarities = self.embeddings @ q / norms

        n = min(n_results, len(self.documents))
        top_idx = np.argsort(similarities)[-n:][::-1]

        return [
            (self.documents[i], self.metadatas[i], float(similarities[i]))
            for i in top_idx
        ]

    def count(self) -> int:
        return len(self.documents)


class GeminiAgent(BaseAgent):
    """Fund Operations Agent using Google Gemini + numpy vector search."""

    def __init__(self):
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        self.client = genai.Client(api_key=api_key)
        self._system_prompt = ""
        self._store = _VectorStore()

    def setup(self, knowledge_dir: str = "data/knowledge_base"):
        """Initialize and load documents into vector store."""
        # 1. Load system prompt
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
        if prompt_path.exists():
            self._system_prompt = prompt_path.read_text(encoding="utf-8")
        print("Gemini agent initialized (gemini-2.5-flash)")

        # 2. Load and index documents
        self._load_documents(knowledge_dir)
        print(f"Vector store ready ({self._store.count()} chunks indexed)")

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using Gemini's free embedding API."""
        all_embeddings = []
        batch_size = 20  # Small batches to avoid rate limits

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            # Retry with backoff for rate limits
            for attempt in range(4):
                try:
                    response = self.client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=batch,
                    )
                    for emb in response.embeddings:
                        all_embeddings.append(emb.values)
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < 3:
                        wait = 2 ** (attempt + 1)
                        print(f"  ⏳ Rate limited, waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        raise

        return all_embeddings

    def _load_documents(self, directory: str):
        """Read files, chunk them, embed, and add to vector store."""
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Directory {directory} not found, skipping.")
            return

        all_chunks = []
        all_metas = []

        for file_path in sorted(dir_path.glob("*")):
            text = self._read_file(file_path)
            if not text:
                continue

            chunks = self._chunk_text(text, max_chars=1000)
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metas.append({"source": file_path.name})
            print(f"  Loaded: {file_path.name} ({len(chunks)} chunks)")

        if not all_chunks:
            return

        # Embed all chunks via Gemini API
        embeddings = self._embed_texts(all_chunks)
        self._store.add(all_chunks, all_metas, embeddings)

    @staticmethod
    def _read_file(file_path: Path) -> str | None:
        """Read a file and return its text content."""
        suffix = file_path.suffix.lower()

        if suffix in (".md", ".txt"):
            return file_path.read_text(encoding="utf-8")

        if suffix == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(file_path))
                return "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
            except ImportError:
                print(
                    f"  ⚠️  Install 'pypdf' to load PDFs: "
                    f"pip install pypdf  (skipping {file_path.name})"
                )
                return None

        return None  # unsupported format

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 1000) -> list[str]:
        """Split text into chunks by paragraph, respecting max_chars."""
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) + 2 > max_chars and current:
                chunks.append(current.strip())
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks if chunks else [text[:max_chars]]

    def ask(self, question: str) -> str:
        """Query vector store for context, then ask Gemini."""
        if self.client is None:
            raise RuntimeError("Agent not set up. Call setup() first.")

        # 1. RAG retrieval
        context = ""
        if self._store.count() > 0:
            q_emb = self._embed_texts([question])[0]
            results = self._store.query(q_emb, n_results=5)
            if results:
                sources = set()
                context_parts = []
                for doc, meta, _score in results:
                    context_parts.append(doc)
                    sources.add(meta["source"])
                context = (
                    "## Relevant context from knowledge base\n"
                    f"Sources: {', '.join(sorted(sources))}\n\n"
                    + "\n---\n".join(context_parts)
                )

        # 2. Build prompt
        if context:
            prompt = f"{context}\n\n## User question\n{question}"
        else:
            prompt = question

        # 3. Call Gemini
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self._system_prompt if self._system_prompt else None,
                ),
            )
            return response.text
        except Exception as e:
            if "blocked" in str(e).lower() or "safety" in str(e).lower():
                return (
                    "Could not generate a response. "
                    "Please try rephrasing your question."
                )
            raise

    def cleanup(self):
        """No-op: everything is in-memory."""
        pass
