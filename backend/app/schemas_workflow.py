from typing import Any

from pydantic import BaseModel, Field


class ValidationResultResponse(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class WorkflowRunResponse(BaseModel):
    """Final state of a completed workflow run. Only agents that exist are included."""

    project_id: int
    workflow_status: str
    current_agent: str | None = None
    requirements: dict[str, Any] | None = None
    project_plan: dict[str, Any] | None = None
    validation_results: dict[str, ValidationResultResponse] = Field(default_factory=dict)

    @classmethod
    def from_state(cls, state: dict) -> "WorkflowRunResponse":
        return cls(
            project_id=state["project_id"],
            workflow_status=state["workflow_status"],
            current_agent=state.get("current_agent"),
            requirements=state.get("requirements"),
            project_plan=state.get("project_plan"),
            validation_results=state.get("validation_results") or {},
        )
