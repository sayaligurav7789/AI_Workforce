# AI Workforce development notes

## Services

- Frontend: `npx vite --config frontend/vite.config.js --host 0.0.0.0 --port 5000`
- Backend: `python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`

The frontend Vite proxy forwards `/api` to the backend. Keep the existing React
structure; backend integration belongs in `frontend/src/services/api.js` and
the existing pages.

## Environment

The backend uses Replit PostgreSQL through `DATABASE_URL`. `SESSION_SECRET` can
sign JWTs by default; `JWT_SECRET` may override it. `GEMINI_API_KEY` is required
before uploading an SRS because embeddings and Requirements Analyst output use
the real Gemini provider. Chroma data and uploaded files are stored under
`data/`.

## Verification

```bash
PYTHONPATH=backend pytest -q backend/tests
npx vite --config frontend/vite.config.js build
```