# AI Workforce

AI Workforce is an SDLC automation platform. The current implementation focuses
on the **Requirements Analyst AI** module:

`SRS PDF → page-aware extraction → Gemini embeddings → project-scoped ChromaDB RAG → structured requirements analysis → PostgreSQL → existing React UI`

## Run on Replit

The project has two services:

- Frontend: Vite/React on port 5000
- Backend: FastAPI on port 8000

The frontend proxies `/api` requests to the backend. Replit workflows are
configured for both services.

Required Replit Secrets/environment variables:

- `DATABASE_URL` — supplied by the Replit PostgreSQL database
- `GEMINI_API_KEY` — required for PDF embeddings, RAG, and analysis
- `JWT_SECRET` — optional when `SESSION_SECRET` is already present; use a long random value for deployments
- `CHROMA_PERSIST_DIRECTORY` — normally `./data/chroma`
- `CORS_ORIGINS` — comma-separated allowed origins

The API documentation is available at `/docs` on the backend service. The
existing frontend remains under `frontend/`; the backend is under `backend/`.

## Scope

Implemented now: authentication, projects, SRS PDF upload and validation,
page-level PDF extraction, chunking, Gemini embeddings, project-isolated
ChromaDB retrieval, RAG queries, structured Requirements Analyst output,
relational persistence, traceable source references, and agent-run status.

Future modules such as Project Manager AI, Developer AI, QA AI, Git automation,
and external integrations are intentionally not implemented yet.
