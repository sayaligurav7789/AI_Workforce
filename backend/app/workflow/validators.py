"""Validation gates. Pure functions of the shared state, so they need no database."""

from .state import COMPLETED, ValidationResult, WorkflowState


def _result(errors: list[str], warnings: list[str]) -> ValidationResult:
    return {"passed": not errors, "errors": errors, "warnings": warnings}


def validate_requirements(state: WorkflowState) -> ValidationResult:
    """Gate between the Requirements Analyst and the Project Manager."""
    errors: list[str] = []
    warnings: list[str] = []
    requirements = state.get("requirements")

    if not requirements:
        errors.append("The Requirements Analyst produced no output.")
    else:
        if requirements.get("status") != COMPLETED:
            errors.append(f"The Requirements Analyst run did not complete (status: {requirements.get('status')}).")
        if not requirements.get("functional_requirements"):
            errors.append("No functional requirements were extracted, so there is nothing to plan.")
        if not requirements.get("user_stories"):
            warnings.append("No user stories were extracted.")
        if not requirements.get("acceptance_criteria"):
            warnings.append("No acceptance criteria were extracted.")
    return _result(errors, warnings)


def validate_project_plan(state: WorkflowState) -> ValidationResult:
    """Gate after the Project Manager (the point where a later Software Architect would start)."""
    errors: list[str] = []
    warnings: list[str] = []
    plan = state.get("project_plan")

    if not plan:
        errors.append("The Project Manager produced no plan.")
    else:
        if plan.get("status") != COMPLETED:
            errors.append(f"The Project Manager run did not complete (status: {plan.get('status')}).")
        if not plan.get("tasks_generated"):
            errors.append("The project plan contains no tasks.")
        if not plan.get("sprints"):
            errors.append("The project plan contains no sprints.")

        # Handoff integrity: the plan must be built from the analyst run of this workflow.
        requirements = state.get("requirements") or {}
        planned_from = plan.get("requirements_run_id")
        produced = requirements.get("agent_run_id")
        if planned_from is not None and produced is not None and planned_from != produced:
            errors.append(
                f"The plan was built from requirements run {planned_from}, "
                f"but this workflow produced run {produced}."
            )
        warnings.extend(str(item) for item in plan.get("warnings") or [])
    return _result(errors, warnings)
