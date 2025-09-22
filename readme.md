# ER-NEXUS: Renal Nutrition & Evidence eXtraction Unified System

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Re-ranking & Response Generation](#re-ranking--response-generation)
- [Data Collection](#data-collection)
- [Deployment-frontend](#uiux)
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

**ER-NEXUS** is a sophisticated, agentic hybrid RAG (Retrieval-Augmented Generation) system designed to provide guidance on diet and microbiome for individuals with Chronic Kidney Disease (CKD) and End-Stage Renal Disease (ESRD). This system is intended for informational purposes and is not a substitute for professional medical advice.

### Key Files in `overview.md`:

- **`app.py`**: This is the main Flask application file. It loads the necessary data from `.pkl` cache files, sets up the vector store and retriever, and defines the routes for the user interface.
- **`config.yaml`**: This file contains all the configuration settings for the application, including model configurations, UI settings, and other parameters.
- **`ernexus/config.py`**: This module defines the Pydantic models for loading and validating the application's configuration from `config.yaml`.
- **`ernexus/chains/qa.py`**: This module is responsible for building the QA (Question-Answering) chains, including both an "answer-only" chain and an agentic chain that provides sources for its answers.
- **`ernexus/retrieval/vectorstore.py`**: This module handles the creation and management of the Chroma vector store, which is used for efficient retrieval of relevant information.

---

## System Architecture

The system's architecture is built around a multi-vector retriever that leverages a Chroma vector store for efficient information retrieval. When a user submits a query, the system identifies relevant text, images, and tables from the cached data to generate a comprehensive answer. This hybrid approach ensures that the responses are both accurate and contextually rich.

For complex queries, the system uses a planner to expand the search, retrieving a larger number of documents to ensure a thorough response. The modular design of the system allows for easy extension and maintenance, with separate components for data loading, retrieval, and response generation.

---

## Re-ranking & Response Generation

After the initial retrieval, the system re-ranks the retrieved documents to prioritize the most relevant information. This ensures that the generated response is based on the most accurate and pertinent data available. The response generation is handled by a QA chain that can operate in two modes: one that provides only the answer and another that includes the sources for the information provided.

---

## Data Collection

The data used by ER-NEXUS is pre-processed and stored in `.pkl` cache files. This approach allows for fast and efficient loading of data at runtime, which is crucial for maintaining a responsive user experience.

### `.pkl` Cache Files

The `data_cache` directory contains the following files:
- `texts.pkl`: Raw text items.
- `text_summaries.pkl`: Cleaned summaries for text data.
- `images.pkl`: A list of base64-encoded images.
- `image_summaries.pkl`: Captions and summaries for the images.
- `tables.pkl`: Table objects.
- `table_summaries.pkl`: Summaries for the tables.

The application is designed to handle cases where some of these files may be missing or unreadable, ensuring robust operation.

---

## Deployment-frontend (UI/UX)

The user interface is built with Flask and is designed to be intuitive and user-friendly. The main page allows users to ask questions and view the generated answers, along with the sources and context used to generate them.

The UI is designed with a clean, glass-like aesthetic, with high contrast for readability. It also includes features like scrollable context boxes and highlighted search terms to enhance the user experience.

---

## Configuration

The application's behavior is controlled by the `config.yaml` file, which is parsed and validated by the `AppConfig` class in `ernexus/config.py`. This file allows you to configure various aspects of the system, including:

- **Application settings**: Title, description, and debug mode.
- **Paths**: Directories for data cache and Chroma DB.
- **Retrieval settings**: Collection name and retrieval parameters.
- **Models**: LLM and embedding models to be used.
- **UI settings**: Sample queries and default UI behavior.
- **Rules**: Dietary rules and limits.

---

## Quickstart (Local)

To run the application locally, follow these steps:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
Set up your environment: Create a .env file with your API keys and other secrets.

Run the app:

Bash

python app.py
Production Deployment (No-Docker)
For production deployment without Docker, you can use a production-ready web server like Gunicorn. The Procfile included in the project is configured for this purpose and can be used with platforms like Heroku or Render.

Production Deployment (Docker)
To deploy the application using Docker, you can use the provided Dockerfile. This will create a container with all the necessary dependencies and run the application using Gunicorn.

API Endpoints
The application exposes the following API endpoints:

GET /: Renders the main page of the application.

POST /: Handles user queries and returns the generated answer.

GET /health: A health check endpoint that returns the status of the application.

Evaluation (Optional)
The system can be evaluated based on the quality and relevance of its responses. This can be done by comparing the generated answers with expert knowledge or by using standard NLP evaluation metrics.

Project Directory Structure
ER-NEXUS/
├─ app.py
├─ config.yaml
├─ requirements.txt
├─ Procfile
├─ .env
├─ Dockerfile
├─ .dockerignore
├─ ernexus/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ formatting.py
│  ├─ prompts/
│  ├─ utils/
│  ├─ io/
│  ├─ retrieval/
│  ├─ chains/
│  ├─ guards/
│  └─ rules/
├─ templates/
├─ static/
├─ data_cache/
└─ render.yaml
