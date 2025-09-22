# ER‑NEXUS (EnteroRenal Nutrition & Evidence eXtraction Unified System)


**Agentic Hybrid RAG** for CKD/ESRD diet & microbiome guidance. The existing `.pkl` caches contains the msot relevant and core knowledgebase for this system. 

> CAUTION: This is experimental, *Not medical advice.* For personal recommendations, consult a renal dietitian/physician.


---


## Features
- **Multimodal retrieval** using your cached summaries (texts/tables/images) with originals in a docstore
- **Agentic planner** adjusts recall depth for complex queries
- **Vision-capable answering** (OpenAI GPT‑4o/4o‑mini) with optional Groq fallback
- **Context viewer** (toggle on/off) with image thumbnails
- **Guardrails** for gibberish/prompt injection
- **Safety notes** for known CKD pitfalls (e.g., star fruit)
- **On‑disk Chroma** persistence for fast startup


---


## Quickstart


```bash
python -m venv .venv && source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
# add your keys to .env


# Place your six .pkl files under ./data_cache exactly as named
# Launch
python app.py