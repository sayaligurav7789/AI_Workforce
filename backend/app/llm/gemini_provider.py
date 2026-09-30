import json
import logging
import time

from pydantic import ValidationError

from ..config import Settings
from ..schemas import RequirementsAnalysis
from .base import LLMProvider

logger = logging.getLogger(__name__)


class ProviderConfigurationError(RuntimeError):
    """Raised when the configured provider cannot be used."""


class GeminiProvider(LLMProvider):
    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise ProviderConfigurationError(
                "GEMINI_API_KEY is not configured. Add it to Replit Secrets before processing documents or analysis."
            )
        from google import genai

        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model
        self._embedding_model = settings.gemini_embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        for attempt in range(2):
            try:
                response = self._client.models.embed_content(
                    model=self._embedding_model,
                    contents=texts,
                )
                return [list(embedding.values) for embedding in response.embeddings]
            except Exception as exc:
                if attempt == 0 and _is_retryable(exc):
                    time.sleep(1.5)
                    continue
                logger.exception("Gemini embedding request failed")
                raise ProviderConfigurationError(f"Embedding provider failed: {exc}") from exc

    def generate_analysis(self, project_name: str, project_description: str, contexts: list[dict]) -> RequirementsAnalysis:
        context_text = _format_contexts(contexts)
        prompt = f"""
You are the Requirements Analyst for the project "{project_name}".
Project description: {project_description or "Not provided"}

Analyze the retrieved SRS excerpts below. Transform explicit customer requirements
into structured software-analysis artifacts. Do not invent features, rules, actors,
priorities, non-functional requirements, constraints, or risks. Label inferred
priorities as INFERRED and use ambiguities for missing details. Every source reference
must exactly match a document/page/source in the supplied excerpts. Use empty lists
when the SRS does not support an artifact. Generate user stories and acceptance
criteria only from supported requirements. For each supported user story, create
at least one concrete acceptance criterion when the SRS states observable behavior.
Do not leave acceptance_criteria empty when the supplied requirements support one.

Return JSON matching the RequirementsAnalysis schema exactly.

RETRIEVED SRS EXCERPTS:
{context_text}
"""
        for attempt in range(2):
            try:
                from google.genai import types

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=_gemini_response_schema(),
                        temperature=0.1,
                        max_output_tokens=16000,
                    ),
                )
                parsed = getattr(response, "parsed", None)
                if parsed is None:
                    parsed = json.loads(response.text)
                return RequirementsAnalysis.model_validate(parsed)
            except Exception as exc:
                if attempt == 0 and (_is_retryable(exc) or isinstance(exc, (json.JSONDecodeError, ValidationError))):
                    time.sleep(1.5)
                    continue
                logger.exception("Gemini structured analysis failed")
                raise ProviderConfigurationError(f"Requirements analysis failed: {exc}") from exc

    def answer_question(self, question: str, contexts: list[dict]) -> str:
        prompt = f"""
Answer the user's question using only the retrieved SRS excerpts below.
If the excerpts do not contain the answer, say that the SRS does not specify it.
Do not invent facts. Do not mention sources that are not supplied.

Question: {question}

RETRIEVED SRS EXCERPTS:
{_format_contexts(contexts)}
"""
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config={"temperature": 0.1},
                )
                return response.text.strip()
            except Exception as exc:
                if attempt == 0 and _is_retryable(exc):
                    time.sleep(1.5)
                    continue
                logger.exception("Gemini RAG answer failed")
                raise ProviderConfigurationError(f"RAG answer failed: {exc}") from exc


def _format_contexts(contexts: list[dict]) -> str:
    return "\n\n".join(
        f"[{item['filename']} page {item['page']} | {item['source']}]\n{item['text']}" for item in contexts
    )


def _is_retryable(error: Exception) -> bool:
    message = str(error).upper()
    return any(marker in message for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "DEADLINE"))


def _gemini_response_schema() -> dict:
    """Gemini rejects Pydantic defaults even though they are valid JSON Schema."""
    schema = RequirementsAnalysis.model_json_schema()

    def remove_defaults(value):
        if isinstance(value, dict):
            return {
                key: remove_defaults(item)
                for key, item in value.items()
                if key != "default"
            }
        if isinstance(value, list):
            return [remove_defaults(item) for item in value]
        return value

    return remove_defaults(schema)