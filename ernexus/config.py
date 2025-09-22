from __future__ import annotations
import os
import yaml
from pydantic import BaseModel, ValidationError


class AppSettings(BaseModel):
    title: str
    description: str
    debug: bool = False


class Paths(BaseModel):
    data_cache_dir: str
    chroma_dir: str


class Retrieval(BaseModel):
    collection_name: str = "er_nexus_multimodal"
    k_initial: int = 6
    k_expand: int = 10


class Models(BaseModel):
    # format "provider/model_name", e.g. "openai/gpt-4o-mini"
    primary_llm: str
    source_llm: str
    fallback_llm: str
    # e.g. "openai/text-embedding-3-large"
    embedding: str


class UI(BaseModel):
    show_context_by_default: bool = False
    enable_model_switch: bool = True
    sample_queries: list[str] = []


class Rules(BaseModel):
    sodium_mg_max: int = 2000
    potassium_mg_limit_flag: int = 2500
    phosphorus_mg_limit_flag: int = 1000
    protein_g_per_kg_ckd: str = "0.6-0.8"
    protein_g_per_kg_dialysis: str = "1.0-1.2"


class AppConfig(BaseModel):
    app: AppSettings
    paths: Paths
    retrieval: Retrieval
    models: Models
    ui: UI
    rules: Rules

    @classmethod
    def from_yaml(cls, path: str) -> "AppConfig":
        # 1) existence
        if not os.path.exists(path):
            _example = _example_yaml()
            raise FileNotFoundError(
                f"config.yaml not found at: {os.path.abspath(path)}\n\n"
                "Create it with content like:\n"
                f"{_example}"
            )

        # 2) non-empty + parse
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            raise ValueError(
                f"config.yaml at {os.path.abspath(path)} is empty. "
                "Populate it with the required sections (app, paths, retrieval, models, ui, rules)."
            )

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML in {path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(
                f"config.yaml at {os.path.abspath(path)} didn’t parse into a mapping. "
                "Ensure it’s valid YAML with top-level keys: app, paths, retrieval, models, ui, rules."
            )

        # 3) basic presence checks for top-level keys
        required = ["app", "paths", "retrieval", "models", "ui", "rules"]
        missing = [k for k in required if k not in data or data[k] is None]
        if missing:
            raise ValueError(
                "config.yaml is missing required sections: " + ", ".join(missing) +
                "\nSee example:\n" + _example_yaml()
            )

        # 4) optional: environment overrides
        #    You can override any nested value with ENV like ERNEXUS__MODELS__PRIMARY_LLM="openai/gpt-4o-mini"
        #    Double-underscore separates levels.
        overlays = _env_overlay(prefix="ERNEXUS__")
        if overlays:
            data = _deep_merge_dicts(data, overlays)

        # 5) pydantic validation
        try:
            return cls(**data)
        except ValidationError as ve:
            raise ValueError(
                "config.yaml failed schema validation. Details:\n"
                f"{ve}\n\nExample config:\n{_example_yaml()}"
            ) from ve


# ---------------- utilities ---------------- #

def _deep_merge_dicts(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base (overlay wins)."""
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge_dicts(out[k], v)
        else:
            out[k] = v
    return out


def _env_overlay(prefix: str = "ERNEXUS__") -> dict:
    """
    Collect ENV variables like:
      ERNEXUS__MODELS__PRIMARY_LLM=openai/gpt-4o-mini
    → {'models': {'primary_llm': 'openai/gpt-4o-mini'}}
    """
    tree: dict = {}
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix):].split("__")
        # normalize to lower & snake-ish
        path = [p.lower() for p in path]
        cur = tree
        for part in path[:-1]:
            cur = cur.setdefault(part, {})
        cur[path[-1]] = _coerce(val)
    return tree


def _coerce(s: str):
    # simple coercions for ints/bools
    sl = s.strip().lower()
    if sl in {"true", "false"}:
        return sl == "true"
    try:
        return int(sl)
    except ValueError:
        return s


def _example_yaml() -> str:
    return (
        "app:\n"
        "  title: \"ER-NEXUS: EnteroRenal Nutrition & Evidence eXtraction Unified System\"\n"
        "  description: \"Agentic hybrid RAG for CKD/ESRD diet & microbiome guidance (not medical advice).\"\n"
        "  debug: true\n"
        "paths:\n"
        "  data_cache_dir: ./data_cache\n"
        "  chroma_dir: ./cache/chroma\n"
        "retrieval:\n"
        "  collection_name: er_nexus_multimodal\n"
        "  k_initial: 6\n"
        "  k_expand: 10\n"
        "models:\n"
        "  primary_llm: openai/gpt-4o-mini\n"
        "  source_llm: openai/gpt-4o\n"
        "  fallback_llm: groq/llama-3.1-70b-versatile\n"
        "  embedding: openai/text-embedding-3-large\n"
        "ui:\n"
        "  show_context_by_default: false\n"
        "  enable_model_switch: true\n"
        "  sample_queries:\n"
        "    - \"Low-potassium snack ideas for CKD stage 3 with diabetes.\"\n"
        "    - \"Summarize probiotic evidence for reducing uremic toxins in ESRD.\"\n"
        "    - \"Compare protein targets for PD vs HD.\"\n"
        "rules:\n"
        "  sodium_mg_max: 2000\n"
        "  potassium_mg_limit_flag: 2500\n"
        "  phosphorus_mg_limit_flag: 1000\n"
        "  protein_g_per_kg_ckd: \"0.6-0.8\"\n"
        "  protein_g_per_kg_dialysis: \"1.0-1.2\"\n"
    )
