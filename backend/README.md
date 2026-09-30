# AI Workforce backend

This backend implements the current milestone: **Requirements Analyst AI**. It
does not implement the future Project Manager, Developer, or QA agents.

## Architecture

1. An authenticated user creates a project.
2. The existing Documents page uploads an SRS PDF to FastAPI.
3. `pypdf` extracts page-level text and a bounded chunker preserves page/source metadata.
4. Gemini creates embeddings; Chroma stores vectors in a collection isolated by project ID.
5. The Requirements Analyst retrieves only that project's chunks and asks Gemini for
   validated structured output.
6. Requirements, user stories, acceptance criteria, dependencies, ambiguities,
   constraints, risks, and agent runs are saved as relational PostgreSQL records.
7. The existing React application reads the API records.

## Secrets and environment

Set these in Replit Secrets/environment variables:

- `DATABASE_URL`: Replit PostgreSQL connection string (provided by the managed database).
- `JWT_SECRET`: a long random signing secret.
- `GEMINI_API_KEY`: Gemini API key.
- `CHROMA_PERSIST_DIRECTORY`: usually `./data/chroma`.
- `CORS_ORIGINS`: comma-separated frontend origins.

Optional settings are documented in `.env.example`. The app uses a local SQLite
development fallback when `DATABASE_URL` is absent, but PostgreSQL is required
for a real deployment. Document processing and analysis fail clearly when
`GEMINI_API_KEY` is absent; the backend never fabricates results.

## Run

From the repository root:

```bash
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```

The interactive API documentation is available at `/docs`.

The frontend runs separately with:

```bash
cd frontend
npm run dev
```

Vite proxies `/api` requests to the backend on port 8000.

## Test

```bash
PYTHONPATH=backend pytest backend/tests
```

The unit tests cover PDF validation, page/source-preserving chunking, and
structured output validation. Provider-backed integration tests should use a
real Gemini secret and a test PostgreSQL/Chroma directory.

## Current limitations

- Analysis is synchronous during the request; a queue/worker can be added later.
- Gemini is the only configured production provider, behind the `LLMProvider`
  interface.
- The current frontend has only the minimum Requirements Analyst result views.

## Future modules

Project Manager AI, Developer AI, QA AI, code execution, Git automation, and
external integrations are intentionally out of scope for this milestone.