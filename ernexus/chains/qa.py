# ernexus/chains/qa.py
from __future__ import annotations
from typing import Dict, List
from textwrap import shorten

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from ernexus.prompts.system_prompts import RENAL_PERSONA
from ernexus.config import AppConfig



def _pick_llm(model_id: str, temperature: float = 0.10):
    provider, name = model_id.split("/", 1)
    if provider == "openai":
        return ChatOpenAI(model=name, temperature=temperature)
    if provider == "groq":
        return ChatGroq(model=name, temperature=temperature)
    raise ValueError(f"Unknown LLM provider: {provider}")

def _parse_docs(docs):
    images_list, texts_list = [], []
    for doc in docs:
        if isinstance(doc, dict) and "data" in doc and "summary" in doc:
            images_list.append(doc)
        elif isinstance(doc, str):
            texts_list.append(doc)
        else:
            try:
                from langchain_core.documents import Document as LCDoc
                if isinstance(doc, LCDoc):
                    texts_list.append(doc.page_content)
                else:
                    texts_list.append(str(doc))
            except Exception:
                texts_list.append(str(doc))
    return {"images": images_list, "texts": texts_list}


def _build_references(ctx: Dict, max_refs: int = 8) -> List[str]:
    """
    Create a compact references list from retrieved context.
    Since we don't have original source URLs, we show short, distinct snippets.
    """
    refs: List[str] = []
    seen = set()

    # Text snippets
    for t in ctx.get("texts", []):
        snippet = shorten(" ".join(t.split()), width=160, placeholder="…")
        if snippet and snippet not in seen:
            refs.append(snippet)
            seen.add(snippet)
        if len(refs) >= max_refs:
            break

    # If room left, add image summaries
    if len(refs) < max_refs:
        for im in ctx.get("images", []):
            s = im.get("summary") or ""
            if not s:
                continue
            snippet = "Image context: " + shorten(" ".join(s.split()), width=140, placeholder="…")
            if snippet and snippet not in seen:
                refs.append(snippet)
                seen.add(snippet)
            if len(refs) >= max_refs:
                break

    return refs


# ...
def _build_messages(payload: Dict, cfg: AppConfig):
    ctx = payload["context"]
    q = payload["question"]

    # compact textual context
    context_text = " ".join(ctx.get("texts", []))

    # Strong formatting instruction is in the system prompt already; add a nudge
    rendered = RENAL_PERSONA.format(context=context_text, question=q)
    parts = [{"type": "text", "text": rendered}]

    # attach images for multimodal models
    for img in ctx.get("images", []):
        parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img['data']}"}
        })

    return [HumanMessage(content=parts)]

def _pick_llm(model_id: str):
    provider, name = model_id.split("/", 1)
    if provider == "openai":
        return ChatOpenAI(model=name, temperature=0)
    if provider == "groq":
        return ChatGroq(model=name, temperature=0)
    raise ValueError(f"Unknown LLM provider: {provider}")


def _planner(question: str, cfg: AppConfig) -> int:
    q = question.lower()
    if any(k in q for k in ["compare", "versus", "vs", "evidence", "systematic", "meta-analysis", "mechanism"]):
        return cfg.retrieval.k_expand
    return cfg.retrieval.k_initial


def build_answer_only(retriever, cfg: AppConfig):
    def with_k(q: str):
        return retriever.get_relevant_documents(q, k=_planner(q, cfg))

    chain = (
        {
            "context": RunnableLambda(lambda payload: with_k(payload["question"])) | RunnableLambda(_parse_docs),
            "question": RunnablePassthrough(),
        }
        | RunnableLambda(lambda d: _build_messages(d, cfg))
        | _pick_llm(cfg.models.primary_llm)
        | StrOutputParser()
    )
    return chain


def build_agentic_chain_with_sources(retriever, cfg: AppConfig):
    def with_k(q: str):
        return retriever.get_relevant_documents(q, k=_planner(q, cfg))

    def attach_references(d: Dict):
        # d == {"context": {...}, "question": "...", "response": "..."} at this stage
        return {
            **d,
            "references": _build_references(d["context"]),
        }

    chain = (
        {
            "context": RunnableLambda(lambda payload: with_k(payload["question"])) | RunnableLambda(_parse_docs),
            "question": RunnablePassthrough(),
        }
        | RunnablePassthrough().assign(
            response=(
                RunnableLambda(lambda d: _build_messages(d, cfg))
                | _pick_llm(cfg.models.source_llm)
                | StrOutputParser()
            )
        )
        | RunnableLambda(attach_references)
    )
    return chain

