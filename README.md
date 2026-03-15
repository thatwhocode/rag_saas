# 🚀 AI SaaS Backend (RAG + Long-Term Memory)

A production-ready, highly scalable asynchronous backend built for AI SaaS applications. This project implements a robust Retrieval-Augmented Generation (RAG) pipeline using local LLMs, persistent chat memory, secure authentication, and background task processing for heavy AI workloads.

## 🏗️ Architecture & Stack

Unlike simple API wrappers, this backend is designed for high availability and clean architecture (Repository/Service patterns, Dependency Injection).

* **API Framework:** FastAPI (Fully Async)
* **LLM Engine:** Ollama (Llama 3 for chat, Nomic-Embed-Text for embeddings)
* **Vector Database:** Qdrant (Async Client)
* **Relational Database:** PostgreSQL + SQLAlchemy 2.0 (Asyncpg) + Alembic
* **Background Tasks:** Celery + Redis (Message Broker & Result Backend)
* **Authentication:** JWT with Token Blacklisting (Redis/Postgres)
* **Containerization:** Docker & Docker Compose

## ✨ Key Features

* **Secure Authentication:** Full JWT-based auth flow including user registration, login, and a secure logout mechanism using a **Token Blacklist** to prevent token reuse.
* **Advanced RAG Pipeline:** Asynchronous document ingestion and vector search using Qdrant.
* **Long-Term Chat Memory:** Conversations are securely stored in PostgreSQL with full CRUD operations.
* **Background AI Tasks:** Heavy LLM operations (e.g., PDF indexing, auto-summarizing the first user message to generate a chat title) are offloaded to Celery workers so the main API remains blazing fast.
* **Cascade Deletions:** Fully managed relational constraints (deleting a chat automatically wipes its message history).
* **Clean Architecture:** Strict separation of concerns (Routers -> Services -> Repositories).

🚀 Quickstart

Get your local environment up and running in minutes:

    Clone the repository:
    Bash

    git clone https://github.com/thatwhocode/rag-saas-backend.git
    cd rag-saas-backend

    Spin up the infrastructure:
    Ensure you have Docker installed, then run:
    Bash

    docker compose up --build -d

        Note: On the first run, the custom entrypoint script will automatically pull the required Ollama models (llama3, nomic-embed-text).

    Access the API:
    Explore the endpoints via the interactive Swagger UI:
    👉 http://localhost:8000/docs

📂 Project Structure

The codebase follows a modular architecture for high scalability:

    src/api/ – FastAPI routers and endpoint definitions.

    src/auth/ – JWT authentication, user management, and token blacklisting.

    src/chat/services/ – Business logic and LLM pipeline orchestration (RAG).

    src/chat/repositories/ – Database interaction layer using SQLAlchemy.

    src/db/ – Models, Alembic migrations, and async session factories.

    src/worker.py – Celery task definitions for background AI processing.

🎯 Next Steps (Roadmap)

    [ ] CI/CD: Integration Tests & GitHub Actions pipeline.

    [ ] Optimization: Redis caching for frequently accessed chat history.

    [ ] Security: Advanced API Rate Limiting for production-grade load.