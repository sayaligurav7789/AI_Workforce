import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import analysis, auth, documents, projects
from .config import get_settings
from .database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title="AI Workforce Requirements Analyst API",
    description="Project-scoped SRS processing, RAG, and Requirements Analyst AI.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(analysis.router)


@app.on_event("startup")
def startup() -> None:
    settings.ensure_directories()
    init_db()


@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "database_configured": bool(settings.database_url),
        "gemini_configured": bool(settings.gemini_api_key),
        "jwt_configured": bool(settings.effective_jwt_secret),
        "provider": "Gemini",
    }