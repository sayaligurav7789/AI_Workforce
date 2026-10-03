"""API-level tests for POST /api/projects/{id}/workflow/run.

The real LangGraph pipeline and the real Project Manager agent run against the SQLite
test database. Only the Requirements Analyst's LLM/vector-store call is replaced, by a
function that stores the analyst's output exactly as the real agent would.
"""

from types import SimpleNamespace

import pytest

from app.agents.pm_context import MissingRequirementsError
from app.agents.project_manager_agent import PlanValidationError
from app.api.workflow import get_vector_store
from app.main import app
from app.models import AgentRun, Document

from .conftest import ScriptedProvider
from .plan_fixtures import registration_plan

RUN = "/api/projects/{}/workflow/run"


@pytest.fixture
def project(client, make_user, make_project):
    user = make_user()
    return SimpleNamespace(user=user, id=make_project(user), headers=user["headers"])


@pytest.fixture
def processed_document(db):
    def _add(project_id: int, status: str = "COMPLETED"):
        db.add(
            Document(
                project_id=project_id, filename="SRS.pdf", file_type="application/pdf",
                file_size=1, storage_path="SRS.pdf", processing_status=status,
            )
        )
        db.commit()

    return _add


@pytest.fixture
def fake_analyst(monkeypatch, db, seed_requirements):
    """Replace only the analyst's LLM call; its saved output matches the real agent's."""
    calls = []

    def _install(project_id: int):
        def fake_run(db_session, project, provider, vector_store):
            calls.append(project.id)
            ids = seed_requirements(project_id)
            run = db_session.get(AgentRun, ids["run_id"])
            analysis = SimpleNamespace(
                functional_requirements=[object()] * 7,
                non_functional_requirements=[object()] * 3,
                user_stories=[object()] * 3,
                acceptance_criteria=[object()] * 7,
                ambiguities=[object()] * 4,
                risks=[],
            )
            return run, analysis

        monkeypatch.setattr("app.workflow.stages.run_requirements_analysis", fake_run)
        app.dependency_overrides[get_vector_store] = lambda: object()
        return ids_holder

    ids_holder = SimpleNamespace(calls=calls)
    ids_holder.install = _install
    return ids_holder


def test_workflow_runs_analyst_then_project_manager_through_the_graph(
    client, project, processed_document, fake_analyst, use_provider
):
    processed_document(project.id)
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    response = client.post(RUN.format(project.id), headers=project.headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["workflow_status"] == "COMPLETED"
    assert body["project_id"] == project.id
    assert body["current_agent"] == "Project Manager AI"
    assert body["requirements"]["functional_requirements"] == 7
    assert body["project_plan"]["tasks_generated"] == 15
    # The Project Manager planned from the analyst run this workflow produced.
    assert body["project_plan"]["requirements_run_id"] == body["requirements"]["agent_run_id"]
    assert set(body["validation_results"]) == {"requirements", "project_plan"}
    assert all(item["passed"] for item in body["validation_results"].values())
    # Future agents are not part of the response.
    assert not {"architecture", "code", "test_results"} & set(body)


def test_missing_srs_stops_before_the_analyst_runs(client, project, fake_analyst, use_provider):
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    response = client.post(RUN.format(project.id), headers=project.headers)

    assert response.status_code == 409
    assert "SRS" in response.json()["detail"]
    assert fake_analyst.calls == []


def test_unprocessed_srs_is_treated_as_missing(client, project, processed_document, fake_analyst, use_provider):
    processed_document(project.id, status="PROCESSING")
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    assert client.post(RUN.format(project.id), headers=project.headers).status_code == 409
    assert fake_analyst.calls == []


def test_project_manager_plan_validation_failure_maps_to_422_and_reports_progress(
    client, project, processed_document, fake_analyst, use_provider, monkeypatch
):
    processed_document(project.id)
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    def reject(*args, **kwargs):
        raise PlanValidationError("The generated project plan failed validation", ["bad dependency"])

    monkeypatch.setattr("app.workflow.stages.run_project_manager", reject)

    response = client.post(RUN.format(project.id), headers=project.headers)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "project_plan" in detail and "failed validation" in detail
    assert "Completed stages: requirements" in detail


def test_project_manager_missing_requirements_maps_to_409(
    client, project, processed_document, fake_analyst, use_provider, monkeypatch
):
    processed_document(project.id)
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    def missing(*args, **kwargs):
        raise MissingRequirementsError("No completed Requirements Analyst output exists for this project.")

    monkeypatch.setattr("app.workflow.stages.run_project_manager", missing)

    assert client.post(RUN.format(project.id), headers=project.headers).status_code == 409


def test_unexpected_agent_failure_maps_to_503(
    client, project, processed_document, fake_analyst, use_provider, monkeypatch
):
    processed_document(project.id)
    fake_analyst.install(project.id)
    use_provider(ScriptedProvider(registration_plan))

    def broken(*args, **kwargs):
        raise RuntimeError("LLM provider unavailable")

    monkeypatch.setattr("app.workflow.stages.run_project_manager", broken)

    response = client.post(RUN.format(project.id), headers=project.headers)
    assert response.status_code == 503
    assert "LLM provider unavailable" in response.json()["detail"]


def test_analyst_failure_stops_the_workflow_before_the_project_manager(
    client, project, processed_document, use_provider, monkeypatch
):
    processed_document(project.id)
    provider = use_provider(ScriptedProvider(registration_plan))
    app.dependency_overrides[get_vector_store] = lambda: object()

    def broken(*args, **kwargs):
        raise RuntimeError("embedding service down")

    monkeypatch.setattr("app.workflow.stages.run_requirements_analysis", broken)

    response = client.post(RUN.format(project.id), headers=project.headers)

    assert response.status_code == 503
    assert "embedding service down" in response.json()["detail"]
    assert provider.calls == []  # the Project Manager never asked the LLM for a plan


def test_workflow_requires_authentication_and_project_ownership(client, project, make_user):
    assert client.post(RUN.format(project.id)).status_code in (401, 403)
    other = make_user()
    assert client.post(RUN.format(project.id), headers=other["headers"]).status_code == 404
