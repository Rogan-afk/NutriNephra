# ER-NEXUS: Renal Nutrition & Evidence eXtraction Unified System

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Re-ranking & Response Generation](#re-ranking--response-generation)
- [Data Collection](#data-collection)
- [Frontend & UI/UX](#frontend--uiux)
- [Configuration](#configuration)
- [Quickstart (Local)](#quickstart-local)
- [Production Deployment (No-Docker)](#production-deployment-no-docker)
- [Production Deployment (Docker)](#production-deployment-docker)
- [API Endpoints](#api-endpoints)
- [Evaluation (Optional)](#evaluation-optional)
- [Project Directory Structure](#project-directory-structure)
- [Citation](#citation)

---

## Overview

**ER-NEXUS** is an advanced, **agentic hybrid RAG** (Retrieval-Augmented Generation) system that provides evidence-based guidance on **diet and microbiome management** for individuals with **Chronic Kidney Disease (CKD)** and **End-Stage Renal Disease (ESRD)**.  

**Disclaimer:** This system is purely experimental.

### Key Components
- **`app.py`** — Main Flask entry point. Initializes retrievers, loads cached data, and routes UI/API.  
- **`config.yaml`** — Central configuration for models, UI, retrieval, and dietary rules.  
- **`ernexus/config.py`** — Pydantic models for config parsing/validation.  
- **`ernexus/chains/qa.py`** — Defines QA pipelines (answer-only vs. answer+citations).  
- **`ernexus/retrieval/vectorstore.py`** — Creates and manages Chroma vector store.  
- **`ernexus/guards/`** — Guards for filtering unsafe or irrelevant inputs.  
- **`ernexus/rules/`** — Encoded dietary rules/constraints.  

---

## System Architecture

The architecture uses a **multi-vector retriever with Chroma** to handle multimodal sources (**text, tables, images**). Queries are expanded with a **planner**, re-ranked, then passed to QA chains for generation.  

### Architecture Flow (Mermaid Diagram)
```mermaid
flowchart TD
    A[User Query] --> B[Retriever: ChromaDB]
    B -->|Text, Images, Tables| C[Planner Expansion]
    C --> D[Re-ranking]
    D --> E[QA Chains]
    E -->|Answer + Sources| F[Frontend/UI]

Re-ranking & Response Generation

Retrieved documents are re-ranked for relevance.

Two QA modes are supported:

Answer-only mode → concise response.

Agentic mode → response with cited sources.

Data Collection

Data is preprocessed and cached in .pkl files for fast load times.

.pkl Cache Files

Located in data_cache/:

texts.pkl — raw text items

text_summaries.pkl — cleaned text summaries

images.pkl — base64-encoded images

image_summaries.pkl — captions & summaries

tables.pkl — table objects

table_summaries.pkl — table summaries

The app handles missing/unreadable files gracefully.

Frontend & UI/UX

Flask-based web app.

Clean glass-like aesthetic with scrollable context panels.

Features:

Query input → contextualized answers

Highlighted terms

Sources listed inline

Configuration

The app is controlled via config.yaml, validated by ernexus/config.py.

Example config.yaml
app:
  title: "ER-NEXUS"
  description: "Renal Nutrition & Evidence eXtraction"
  debug: true

paths:
  cache_dir: "./data_cache"
  chroma_db: "./chroma"

retrieval:
  collection: "renal_nutrition"
  top_k: 5

models:
  llm: "gpt-4o"
  embedding: "text-embedding-3-large"

ui:
  sample_queries:
    - "What probiotics are recommended for CKD patients?"
    - "Summarize the effect of phosphorus intake on ESRD."

rules:
  sodium_limit: 2000
  potassium_limit: 2500
  phosphorus_limit: 1000

Quickstart (Local)

Install dependencies

pip install -r requirements.txt


Set up environment

cp .env.example .env


Add your API keys in .env.

Run the app

python app.py

Production Deployment (No-Docker)

Run with Gunicorn:

gunicorn app:app --workers 4 --bind 0.0.0.0:8000


Example Procfile:

web: gunicorn app:app --workers=4 --bind=0.0.0.0:$PORT

Production Deployment (Docker)

Build image

docker build -t ernexus .


Run container

docker run -p 8000:8000 ernexus

API Endpoints
Method	Endpoint	Description
GET	/	Main UI page
POST	/	Accepts query, returns JSON
GET	/health	Health check status
Evaluation (Optional)

Evaluation can be performed using:

Expert review (manual validation against domain experts)

NLP metrics: BLEU, ROUGE, BERTScore

Project Directory Structure
ER-NEXUS/
├─ app.py
├─ config.yaml
├─ requirements.txt
├─ Procfile
├─ .env
├─ Dockerfile
├─ .dockerignore
├─ render.yaml
├─ ernexus/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ formatting.py
│  ├─ prompts/
│  │   ├─ qa_prompts.py
│  │   └─ retrieval_prompts.py
│  ├─ utils/
│  │   ├─ logger.py
│  │   └─ helpers.py
│  ├─ io/
│  │   └─ loaders.py
│  ├─ retrieval/
│  │   ├─ vectorstore.py
│  │   └─ multi_retriever.py
│  ├─ chains/
│  │   ├─ qa.py
│  │   └─ planner.py
│  ├─ guards/
│  │   ├─ input_guard.py
│  │   └─ safety.py
│  └─ rules/
│      └─ diet_rules.yaml
├─ templates/
│  ├─ base.html
│  ├─ chat.html
│  └─ results.html
├─ static/
│  ├─ css/
│  └─ js/
└─ data_cache/
   ├─ texts.pkl
   ├─ text_summaries.pkl
   ├─ images.pkl
   ├─ image_summaries.pkl
   ├─ tables.pkl
   └─ table_summaries.pkl

Citation

If you use ER-NEXUS in your research, please cite:

@misc{ernexus2025,
  title   = {ER-NEXUS: Renal Nutrition & Evidence eXtraction Unified System},
  author  = {Your Name},
  year    = {2025},
  note    = {Available at: https://github.com/your-repo/ernexus}
}
