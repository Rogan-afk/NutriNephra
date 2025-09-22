import os
import pickle
from dotenv import load_dotenv
from flask import Flask, render_template, request
import re, base64
from typing import List, Dict
import markdown2  # for rendering markdown → HTML

from ernexus.config import AppConfig
from ernexus.utils.logging import log
# We’ll use a local loader in this file (more robust for your pickles)
# from ernexus.io.cache_loader import load_cached_data  # (not used here)
from ernexus.retrieval.vectorstore import build_vectorstore
from ernexus.retrieval.multi_vector import build_multivector_retriever
from ernexus.chains.qa import build_agentic_chain_with_sources, build_answer_only
from ernexus.guards.validator import validate_query
from ernexus.rules.counsel import diet_safety_notes
from ernexus.formatting import (
    sanitize_summary,
    bulletize,
    short_snippet,
    format_image_caption,
    tighten_answer,
)

# --------------------------------------------------------------------------------------
# Env & App
# --------------------------------------------------------------------------------------
load_dotenv()
config = AppConfig.from_yaml("config.yaml")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")


#image context helpers
def _is_base64_str(s: str) -> bool:
    try:
        # quick check
        if not isinstance(s, str) or "," in s or " " in s:
            return False
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False

def _ensure_b64(x) -> str:
    """Accepts bytes or str; always returns a clean base64 string (no data URI)."""
    if isinstance(x, bytes):
        return base64.b64encode(x).decode("utf-8")
    if isinstance(x, str):
        return x if _is_base64_str(x) else base64.b64encode(x.encode("utf-8")).decode("utf-8")
    # last resort: stringify then b64
    return base64.b64encode(str(x).encode("utf-8")).decode("utf-8")

def build_keyword_image_hits(query: str, images: List, image_summaries: List[str], k: int = 4) -> List[Dict[str, str]]:
    """
    Pick up to k images by simple keyword scoring on image_summaries; includes <mark> highlighting.
    Falls back to the first k images if no keyword hits.
    """
    terms = [w.lower() for w in re.findall(r"[A-Za-z0-9]{3,}", query)]
    N = min(len(images), len(image_summaries))
    scored = []
    for i in range(N):
        cap = (image_summaries[i] or "").strip()
        if not cap:
            continue
        l = cap.lower()
        score = 0
        first_pos = None
        for term in terms:
            for m in re.finditer(re.escape(term), l):
                score += 1
                if first_pos is None:
                    first_pos = m.start()
        if score > 0 and first_pos is not None:
            scored.append((score, i, cap, first_pos))

    out = []
    if scored:
        scored.sort(key=lambda x: (-x[0], x[3]))
        picks = [i for _, i, _, _ in scored[:k]]
    else:
        picks = list(range(min(k, N)))

    for i in picks:
        cap = (image_summaries[i] or "").strip()
        # highlight terms
        for term in terms:
            cap = re.sub(f"({re.escape(term)})", r"<mark>\1</mark>", cap, flags=re.I)
        out.append({"data": _ensure_b64(images[i]), "summary": cap})

    return out

#search helpers
def _tokenize(q: str) -> List[str]:
    # keep simple alphanumeric words ≥3 chars
    return [w.lower() for w in re.findall(r"[A-Za-z0-9]{3,}", q)]

def _excerpt_hit(text: str, hit_idx: int, pad: int = 160) -> str:
    """Return a centered excerpt around a hit index with ellipses."""
    start = max(0, hit_idx - pad)
    end = min(len(text), hit_idx + pad)
    pre = "…" if start > 0 else ""
    post = "…" if end < len(text) else ""
    return f"{pre}{text[start:end].strip()}{post}"

def build_keyword_excerpts(query: str, text_pool: List[str], k: int = 5) -> List[Dict[str, str]]:
    """
    Very small, dependency-free keyword scorer:
    - scores by # of term hits (case-insensitive)
    - returns up to k excerpts with <mark> highlighting
    - pulls from summaries first; if you pass texts, ensure they are strings
    """
    terms = _tokenize(query)
    if not terms:
        return []

    scored: List[tuple] = []  # (score, idx, text, first_hit_pos)
    for i, raw in enumerate(text_pool):
        if not isinstance(raw, str) or not raw.strip():
            continue
        t = raw.strip()
        l = t.lower()
        # count hits, remember earliest hit position
        score = 0
        first_pos = None
        for term in terms:
            for m in re.finditer(re.escape(term), l):
                score += 1
                if first_pos is None:
                    first_pos = m.start()
        if score > 0 and first_pos is not None:
            scored.append((score, i, t, first_pos))

    if not scored:
        return []

    # sort by score desc, then by earlier hit
    scored.sort(key=lambda x: (-x[0], x[3]))

    excerpts: List[Dict[str, str]] = []
    used = 0
    for score, idx, t, pos in scored:
        hit_excerpt = _excerpt_hit(t, pos, pad=160)
        # highlight *all* term occurrences in the excerpt (case-insensitive)
        def _hi(s: str) -> str:
            for term in terms:
                s = re.sub(f"({re.escape(term)})", r"<mark>\1</mark>", s, flags=re.I)
            return s
        html = _hi(hit_excerpt)
        excerpts.append({"text": html, "page_number": "N/A"})
        used += 1
        if used >= k:
            break
    return excerpts

# --------------------------------------------------------------------------------------
# Robust cache loader for your pickles (handles unstructured class pickles safely)
# --------------------------------------------------------------------------------------
def load_cached_data_local(directory: str = "./data_cache"):
    def _load(name):
        path = os.path.join(directory, name)
        with open(path, "rb") as f:
            return pickle.load(f)

    tables = texts = images = []
    text_summaries = table_summaries = image_summaries = []

    try:
        tables = _load("tables.pkl")
    except Exception:
        tables = []
    try:
        table_summaries = _load("table_summaries.pkl")
    except Exception:
        table_summaries = []
    try:
        images = _load("images.pkl")  # base64 strings list
    except Exception:
        images = []
    try:
        image_summaries = _load("image_summaries.pkl")
    except Exception:
        image_summaries = []
    try:
        text_summaries = _load("text_summaries.pkl")
    except Exception:
        text_summaries = []

    # texts.pkl often has objects from `unstructured`—skip gracefully
    try:
        texts = _load("texts.pkl")
        texts = [str(t) for t in texts]
    except Exception:
        texts = []

    # Clean summaries for better UI
    clean_text_summaries = [sanitize_summary(s) for s in text_summaries]
    clean_table_summaries = [sanitize_summary(s) for s in table_summaries]
    clean_image_summaries = [sanitize_summary(s) for s in image_summaries]

    return {
        "tables": tables,
        "texts": texts,
        "images": images,
        "text_summaries": clean_text_summaries,
        "table_summaries": clean_table_summaries,
        "image_summaries": clean_image_summaries,
    }


cached = load_cached_data_local("./data_cache")
tables = cached["tables"]
texts = cached["texts"]
images = cached["images"]
text_summaries = cached["text_summaries"]
table_summaries = cached["table_summaries"]
image_summaries = cached["image_summaries"]


# --------------------------------------------------------------------------------------
# Vector store + retriever
# --------------------------------------------------------------------------------------
vectorstore, docstore, id_key = build_vectorstore(
    summaries={"texts": text_summaries, "images": image_summaries, "tables": table_summaries},
    originals={"texts": texts, "images": images, "tables": tables},
    cfg=config,
)
retriever = build_multivector_retriever(vectorstore, docstore, id_key)


# --------------------------------------------------------------------------------------
# QA chains
# --------------------------------------------------------------------------------------
answer_only = build_answer_only(retriever, config)
chain_with_sources = build_agentic_chain_with_sources(retriever, config)


# --------------------------------------------------------------------------------------
# Helpers for UI
# --------------------------------------------------------------------------------------
def build_references(ctx: dict, max_refs: int = 8):
    """Create a compact references list from retrieved context (texts first, then image captions)."""
    refs = []
    seen = set()

    for t in ctx.get("texts", []):
        snip = short_snippet(t, width=160)
        if snip and snip not in seen:
            refs.append(snip)
            seen.add(snip)
        if len(refs) >= max_refs:
            return refs

    for im in ctx.get("images", []):
        cap = im.get("summary") or ""
        if not cap:
            continue
        snip = "Image: " + short_snippet(cap, width=140)
        if snip and snip not in seen:
            refs.append(snip)
            seen.add(snip)
        if len(refs) >= max_refs:
            break

    return refs


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/", methods=["GET", "POST"])
def index():
    # Defaults
    answer_html = None
    references = []
    context_texts = []
    context_images = []


    
    # UI config
    sample_queries = config.ui.sample_queries
    show_context_default = config.ui.show_context_by_default

    if request.method == "POST":
        user_q = request.form.get("question", "").strip()

        # Guard checks
        ok, guard_msg = validate_query(user_q)
        if not ok:
            # guard_msg is plain text; render as small HTML paragraph
            guard_html = markdown2.markdown(guard_msg) if guard_msg else "<p>Query rejected.</p>"
            return render_template(
                "index.html",
                answer=guard_html,  # template uses {{ answer|safe }}
                references=references,
                context_texts=context_texts,
                context_images=context_images,
                sample_queries=sample_queries,
                show_context_default=show_context_default,
                cfg=config,
            )

        # Run RAG chain with sources
        result = chain_with_sources.invoke({"question": user_q})
        raw_answer = result.get("response", "") or ""
        ctx = result.get("context", {"texts": [], "images": []}) or {}

        # Optional tailored notes (your custom logic)
        notes = diet_safety_notes(user_q)
        if notes:
            # Add as a final bullet to answer before tightening → it will be kept concise
            raw_answer += f"\n\n- Safety note: {notes}"

        # Tighten/clean the answer, enforce bullets, remove “consult your provider” phrasing
        tidy_answer = tighten_answer(raw_answer, max_line=120)
        # Render to HTML so bullets/markdown look correct in UI
        answer_html = markdown2.markdown(tidy_answer)

        # Build references list (compact)
        references = build_references(ctx, max_refs=8)

        # Prepare UI context (formatted)
          # Prepare UI context (formatted from retriever)
        for txt in ctx.get("texts", []):
            pretty = bulletize(txt, max_line=90)
            context_texts.append({"text": pretty, "page_number": "N/A"})

        # Images from retriever → normalize to base64 + tidy captions
        for im in ctx.get("images", []):
            raw = im.get("data")
            cap = im.get("summary") or ""
            b64 = _ensure_b64(raw)
            cap = format_image_caption(cap, width=120)
            context_images.append({"data": b64, "summary": cap})

        # ---- Fallbacks: keyword excerpts (text) and images ----
        if not context_texts:
            fallback_pool = text_summaries if text_summaries else texts
            kw_excerpts = build_keyword_excerpts(user_q, fallback_pool, k=5)
            if kw_excerpts:
                context_texts = kw_excerpts

        if not context_images:
            # find relevant images by caption keywords; highlight with <mark>
            context_images = build_keyword_image_hits(user_q, images, image_summaries, k=4)

        # If you also want references even when RAG found nothing:
        if not references:
            refs_from_kw = [re.sub(r"</?mark>", "", e.get("text", "")) for e in (context_texts or []) if e.get("text")]
            references = refs_from_kw[:8]


    # Render
    return render_template(
        "index.html",
        answer=answer_html,            # already HTML; template should do {{ answer|safe }}
        references=references,         # list of snippets
        context_texts=context_texts,   # [{text, page_number}]
        context_images=context_images, # [{data, summary}]
        sample_queries=sample_queries,
        show_context_default=show_context_default,
        cfg=config,
    )


if __name__ == "__main__":
    app.run(debug=config.app.debug)
