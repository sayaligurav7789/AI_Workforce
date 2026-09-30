import json
import logging
import time

from pydantic import ValidationError

from ..config import Settings
from ..schemas import RequirementsAnalysis
from ..schemas_pm import ProjectPlan
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

                return [
                    list(embedding.values)
                    for embedding in response.embeddings
                ]

            except Exception as exc:
                if attempt == 0 and _is_retryable(exc):
                    time.sleep(1.5)
                    continue

                logger.exception("Gemini embedding request failed")
                raise ProviderConfigurationError(
                    f"Embedding provider failed: {exc}"
                ) from exc

    def generate_analysis(
        self,
        project_name: str,
        project_description: str,
        contexts: list[dict],
    ) -> RequirementsAnalysis:
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
                if attempt == 0 and (
                    _is_retryable(exc)
                    or isinstance(
                        exc,
                        (json.JSONDecodeError, ValidationError),
                    )
                ):
                    time.sleep(1.5)
                    continue

                logger.exception("Gemini structured analysis failed")
                raise ProviderConfigurationError(
                    f"Requirements analysis failed: {exc}"
                ) from exc

    def generate_project_plan(
        self,
        project_name: str,
        project_description: str,
        requirements: dict,
        project_info: dict,
        feedback: list[str] | None = None,
    ) -> ProjectPlan:
        base_prompt = _project_plan_prompt(
            project_name,
            project_description,
            requirements,
            project_info,
        )

        problems = list(feedback or [])

        # Maximum 3 attempts.
        # Retry delays for transient Gemini failures:
        # Attempt 1 -> 503 -> wait 2 seconds
        # Attempt 2 -> 503 -> wait 5 seconds
        # Attempt 3 -> fail
        retry_delays = [2, 5]

        for attempt in range(3):
            prompt = base_prompt

            if problems:
                prompt += (
                    "\n\nYOUR PREVIOUS PLAN WAS REJECTED. Return a corrected, complete plan "
                    "that fixes every problem below without dropping valid content:\n- "
                    + "\n- ".join(problems[:40])
                )

            try:
                from google.genai import types

                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=_gemini_response_schema(ProjectPlan),
                        temperature=0.2,
                        max_output_tokens=32000,
                    ),
                )

                parsed = getattr(response, "parsed", None)

                if parsed is None:
                    parsed = json.loads(response.text)

                if isinstance(parsed, ProjectPlan):
                    return parsed

                return ProjectPlan.model_validate(parsed)

            except Exception as exc:
                is_validation_error = isinstance(
                    exc,
                    (json.JSONDecodeError, ValidationError),
                )

                is_retryable_error = _is_retryable(exc)

                if attempt < 2 and (
                    is_retryable_error or is_validation_error
                ):
                    if is_validation_error:
                        problems = [
                            *problems,
                            f"Output was not valid against the schema: {str(exc)[:600]}",
                        ]

                    delay = retry_delays[attempt]

                    logger.warning(
                        "Gemini project plan generation failed on attempt %s/3. "
                        "Retrying in %s seconds. Error: %s",
                        attempt + 1,
                        delay,
                        exc,
                    )

                    time.sleep(delay)
                    continue

                logger.exception(
                    "Gemini project plan generation failed after %s attempt(s)",
                    attempt + 1,
                )

                raise ProviderConfigurationError(
                    f"Project plan generation failed: {exc}"
                ) from exc

    def answer_question(
        self,
        question: str,
        contexts: list[dict],
    ) -> str:
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
                raise ProviderConfigurationError(
                    f"RAG answer failed: {exc}"
                ) from exc


def _project_plan_prompt(
    project_name: str,
    project_description: str,
    requirements: dict,
    project_info: dict,
) -> str:
    start = project_info.get("start_date") or "not provided"
    due = project_info.get("due_date") or "not provided"

    return f"""
You are the Project Manager AI for the software project "{project_name}".
Project description: {project_description or "Not provided"}
Project start date: {start}
Project due date: {due}
Team size, velocity and working calendar: NOT PROVIDED.

Your ONLY input is the validated output of the Requirements Analyst, given below as JSON.
Do not re-derive requirements and do not assume anything about the SRS beyond this JSON.
Turn it into an execution plan.

GROUNDING (the most important rule)
- Every task must be traceable. Cite ids exactly as they appear in the input (for example
  REQ-3, US-2, AC-5, NFR-1, CON-1, DEP-1, AMB-1). Never invent an id.
- related_requirement_id / related_story_id: the single most relevant requirement / user story.
- related_artifact_ids: any other supporting ids (acceptance criteria, non-functional
  requirements, constraints, dependencies, ambiguities, risks).
- grounding = EXPLICIT when the input directly calls for the work. Cite at least one id.
- grounding = INFERRED for reasonable engineering prerequisites the input implies but does not
  state (for example, a schema migration needed to store accounts). Explain in `rationale`, and
  tie the task to a cited id or to a task that depends on it.
- grounding = AMBIGUOUS when the input is too vague to build safely (cite the AMB id and say in
  `rationale` what is unknown). Prefer a small "decide/clarify" task over guessing.
- grounding = UNKNOWN when required information is unavailable. Explain in `rationale`.
- Do NOT add features, integrations or capabilities the requirements do not support. If the
  input does not mention social login, payments, biometrics, OAuth, etc., they must not appear.
  Where the input says something is unspecified, do not fill the gap with an invented decision.

TASKS
- Break every functional requirement and user story into concrete, implementable tasks.
  Usual work includes API/business logic, validation, data storage, UI, security handling,
  external integrations, automated tests, and performance verification when a non-functional
  requirement calls for it. Only include work the input justifies.
- Each non-functional requirement and each constraint must be addressed by at least one task.
- story_points must be one of 1, 2, 3, 5, 8, 13. Split anything larger than 13.
- suggested_role must be one of: Frontend Developer, Backend Developer, Full Stack Developer,
  Database Engineer, AI/ML Engineer, DevOps Engineer, QA Engineer, Security Engineer,
  UI/UX Designer. Choose the role whose skills the work actually needs.
- acceptance_criteria: concrete, testable statements for that task, taken from or consistent
  with the cited acceptance criteria.
- Group tasks under epics (epic_id). An epic is a coherent feature area.

DEPENDENCIES (one flat list, not repeated on tasks)
- Each entry: task_id (the dependent task), depends_on_task_id, dependency_type, description,
  is_blocking.
- TECHNICAL (code/API needed first), DATA (data/schema needed first), INTEGRATION (a
  component must exist before joining), PREREQUISITE (must finish before starting),
  EXTERNAL (something outside the plan, such as a third-party service or a pending decision).
- EXTERNAL entries must leave depends_on_task_id null and name the external thing in the description.
- is_blocking = true when the task cannot start until the dependency is resolved.
- The graph must have no cycles.

SPRINTS
- Choose the number of sprints from the amount of work, dependency depth and priority. Do not
  use a fixed number. List sprints in chronological order.
- Assign each task to exactly one sprint using its sprint_id in the task's `sprint` field.
- A task's sprint must be the same as or later than the sprint of every task it depends on.
- Put high-priority and foundational work first.
- start_date and end_date: use ISO dates (YYYY-MM-DD) ONLY if a project start date was provided
  above AND you can derive them without guessing team capacity. Otherwise set both to null.
- capacity_notes: state only what is known. Team size and velocity are not provided; say so
  rather than inventing numbers.

MILESTONES, RISKS, DEFINITION OF DONE
- Milestones mark completion of meaningful groups of tasks (task_ids). Optionally set target_sprint.
- Risks must be specific to this project and its requirements (use the ambiguities, constraints
  and dependencies), not generic advice. Give impact, likelihood, a concrete mitigation and
  related_tasks.
- definition_of_done: items appropriate for this project (implementation complete, acceptance
  criteria met, tests passing, security requirements met, integration verified, documentation
  updated), phrased for this project.
- assumptions: list only assumptions you had to make. Use an empty list if none.

IDS: epic_id E1, E2...; task_id T1, T2...; sprint_id S1, S2...; milestone_id M1...; risk_id RK1...

Return JSON matching the ProjectPlan schema exactly.

REQUIREMENTS ANALYST OUTPUT:
{json.dumps(requirements, indent=1, default=str)}
"""


def _format_contexts(contexts: list[dict]) -> str:
    return "\n\n".join(
        f"[{item['filename']} page {item['page']} | {item['source']}]\n{item['text']}"
        for item in contexts
    )


def _is_retryable(error: Exception) -> bool:
    message = str(error).upper()

    return any(
        marker in message
        for marker in (
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "DEADLINE",
        )
    )


def _gemini_response_schema(model=RequirementsAnalysis) -> dict:
    """Gemini rejects Pydantic defaults even though they are valid JSON Schema."""
    schema = model.model_json_schema()

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