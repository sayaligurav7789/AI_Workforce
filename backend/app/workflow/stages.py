"""The workflow stages that exist today.

Each stage wraps an existing agent function without changing it, converts the agent's
result into a small summary for the shared state, and turns the agent's known failures
into classified ``StageError`` values the graph can route.

Software Architect, Developer and QA are intentionally absent: they do not exist yet,
and no placeholder implementations are provided for them.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents.pm_context import MissingRequirementsError
from ..agents.project_manager_agent import PlanValidationError, RunInProgressError, run_project_manager
from ..agents.requirements_agent import run_requirements_analysis
from ..llm.base import LLMProvider
from ..models import Document, Project
from ..rag.vector_store import ProjectVectorStore
from .graph import Stage
from .state import IN_PROGRESS, MISSING_INPUT, PLAN_INVALID, StageError, WorkflowState
from .validators import validate_project_plan, validate_requirements


@dataclass
class WorkflowDeps:
    """Runtime dependencies the agents need. They are not part of the serialisable state."""

    db: Session
    project: Project
    provider: LLMProvider
    vector_store: ProjectVectorStore


def requirements_stage(deps: WorkflowDeps) -> Stage:
    def run(state: WorkflowState) -> dict:
        has_document = deps.db.scalar(
            select(Document.id).where(Document.project_id == deps.project.id, Document.processing_status == "COMPLETED")
        )
        if not has_document:
            raise StageError(MISSING_INPUT, "Upload and finish processing an SRS before analysis")

        agent_run, analysis = run_requirements_analysis(deps.db, deps.project, deps.provider, deps.vector_store)
        output = agent_run.output_summary or {}
        return {
            "requirements": {
                "agent_run_id": agent_run.id,
                "status": agent_run.status,
                "documents_analyzed": output.get("documents_analyzed"),
                "functional_requirements": len(analysis.functional_requirements),
                "non_functional_requirements": len(analysis.non_functional_requirements),
                "user_stories": len(analysis.user_stories),
                "acceptance_criteria": len(analysis.acceptance_criteria),
                "ambiguities": len(analysis.ambiguities),
                "risks": len(analysis.risks),
            }
        }

    return Stage(
        key="requirements",
        agent="Requirements Analyst AI",
        node_name="requirements_analyst_node",
        validation_name="validate_requirements",
        run=run,
        validate=validate_requirements,
    )


def project_manager_stage(deps: WorkflowDeps) -> Stage:
    def run(state: WorkflowState) -> dict:
        try:
            agent_run = run_project_manager(deps.db, deps.project, deps.provider)
        except MissingRequirementsError as exc:
            raise StageError(MISSING_INPUT, str(exc)) from exc
        except RunInProgressError as exc:
            raise StageError(IN_PROGRESS, str(exc)) from exc
        except PlanValidationError as exc:
            raise StageError(PLAN_INVALID, str(exc)) from exc

        output = agent_run.output_summary or {}
        return {
            "project_plan": {
                "agent_run_id": agent_run.id,
                "status": agent_run.status,
                "requirements_run_id": output.get("requirements_run_id"),
                "epics": output.get("epics"),
                "tasks_generated": output.get("tasks_generated"),
                "sprints": output.get("sprints"),
                "milestones": output.get("milestones"),
                "risks": output.get("risks"),
                "total_story_points": output.get("total_story_points"),
                "attempts": output.get("attempts"),
                "warnings": output.get("warnings") or [],
            }
        }

    return Stage(
        key="project_plan",
        agent="Project Manager AI",
        node_name="project_manager_node",
        validation_name="validate_project_plan",
        run=run,
        validate=validate_project_plan,
    )


def default_stages(deps: WorkflowDeps) -> list[Stage]:
    """The executable pipeline today: Requirements Analyst -> Project Manager.

    To add the Software Architect later, append its Stage here
    (node ``architect_node``, gate ``validate_architecture``).
    """
    return [requirements_stage(deps), project_manager_stage(deps)]
