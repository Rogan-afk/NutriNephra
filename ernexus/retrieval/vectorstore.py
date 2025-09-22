# ernexus/retrieval/vectorstore.py
import uuid
from typing import Dict, List
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.storage import InMemoryStore
from langchain_core.documents import Document

from ernexus.config import AppConfig


def _normalize_embedding_id(eid: str) -> str:
    """Accept 'text-embedding-3-large' or 'openai/text-embedding-3-large' and return bare model name."""
    return eid.split("/", 1)[1] if "/" in eid else eid


def build_vectorstore(
    summaries: Dict[str, List[str]],
    originals: Dict[str, List],
    cfg: AppConfig,
):
    """
    Create a Chroma vector store and populate with summary docs; originals go into docstore.
    Returns (vectorstore, docstore, id_key).
    """
    # Ensure persist path exists (Windows-friendly)
    persist_dir = Path(cfg.paths.chroma_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    embed_model = _normalize_embedding_id(cfg.models.embedding)
    embedder = OpenAIEmbeddings(model=embed_model)

    vectorstore = Chroma(
        collection_name=cfg.retrieval.collection_name,
        embedding_function=embedder,
        persist_directory=str(persist_dir),  # persistence is auto-managed; no .persist() call needed
    )
    docstore = InMemoryStore()
    id_key = "doc_id"

    def add_group(group_name: str):
        raw = (originals.get(group_name, []) or [])
        sums = (summaries.get(group_name, []) or [])
        n = min(len(raw), len(sums))
        if n <= 0:
            return

        raw = raw[:n]
        sums = sums[:n]
        ids = [str(uuid.uuid4()) for _ in range(n)]

        summary_docs = [
            Document(page_content=sums[i], metadata={id_key: ids[i], "modality": group_name})
            for i in range(n)
        ]
        vectorstore.add_documents(summary_docs)

        if group_name == "images":
            # images are dicts: {"data": base64, "summary": str}
            docstore.mset([(ids[i], {"data": raw[i], "summary": sums[i]}) for i in range(n)])
        else:
            # texts/tables are strings
            docstore.mset(list(zip(ids, raw)))

    for key in ("texts", "tables", "images"):
        add_group(key)

    # NOTE: no vectorstore.persist() on langchain-chroma; it’s automatic with persist_directory
    return vectorstore, docstore, id_key
