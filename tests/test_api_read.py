from collections.abc import Callable, Iterator
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.domain.tir import TechnicalIntakeRequest
from app.main import app
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base, ProjectFolderInventory, ReconciliationResult
from app.storage.repositories import TIRRecordRepository


def make_tir(project_name: str, *, status: str = "IN_PROGRESS") -> TechnicalIntakeRequest:
    return TechnicalIntakeRequest(
        created=datetime(2026, 6, 1, tzinfo=UTC),
        secretary_approval=True,
        mise_hod="ABED",
        registry_confirmation=True,
        registry_file_ref=f"MISE-ABED-{project_name[-1]}",
        organisation="Betio Town Council",
        project_name=project_name,
        service_request="Inspection",
        project_location="Betio",
        project_status=status,
        contact_person="Example Contact",
        contact_email=f"{project_name[-1]}@example.test",
        funding_source="Government",
    )


def make_session_override() -> Callable[[], Iterator[Session]]:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with session_scope(engine) as session:
        repository = TIRRecordRepository()
        first = repository.add(session, make_tir("Project 1"), smartsheet_row_id="row-1")
        second = repository.add(
            session,
            make_tir("Project 2", status="COMPLETED"),
            smartsheet_row_id="row-2",
        )
        session.add(
            ProjectFolderInventory(
                folder_path="C:/MISE/MISE-ABED-1 - Project 1",
                folder_name="MISE-ABED-1 - Project 1",
                parent_path="C:/MISE",
                inferred_registry_file_ref="MISE-ABED-1",
                inferred_project_name="Project 1",
                file_count=2,
            )
        )
        session.add(
            ReconciliationResult(
                tir_record_id=first.id,
                registry_file_ref=first.registry_file_ref,
                project_name=first.project_name,
                category="MATCHED",
                confidence_score=100,
                matched_folder_path="C:/MISE/MISE-ABED-1 - Project 1",
                reasons=["Exact registry reference match"],
            )
        )
        session.add(
            ReconciliationResult(
                tir_record_id=second.id,
                registry_file_ref=second.registry_file_ref,
                project_name=second.project_name,
                category="MISSING_FOLDER",
                confidence_score=0,
                matched_folder_path=None,
                reasons=["No folder matched registry reference or project name"],
            )
        )

    def override() -> Iterator[Session]:
        with session_scope(engine) as session:
            yield session

    return override


def make_client() -> TestClient:
    app.dependency_overrides[get_db_session] = make_session_override()
    return TestClient(app)


def test_health_endpoint() -> None:
    response = make_client().get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tir_list_supports_filtering_pagination_and_sorting() -> None:
    response = make_client().get(
        "/api/v1/tir",
        params={
            "project_status": "IN_PROGRESS",
            "funding_source": "Government",
            "department_code": "ABED",
            "location": "Betio",
            "limit": 1,
            "offset": 0,
            "sort_by": "project_name",
            "sort_order": "asc",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["project_name"] == "Project 1"


def test_tir_detail_returns_record() -> None:
    test_client = make_client()
    list_payload = test_client.get("/api/v1/tir", params={"registry_file_ref": "MISE-ABED-1"}).json()
    record_id = list_payload["items"][0]["id"]

    response = test_client.get(f"/api/v1/tir/{record_id}")

    assert response.status_code == 200
    assert response.json()["registry_file_ref"] == "MISE-ABED-1"


def test_projects_endpoint_filters_registry_reference() -> None:
    response = make_client().get("/api/v1/projects", params={"registry_file_ref": "MISE-ABED-1"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["inferred_project_name"] == "Project 1"


def test_reconciliation_endpoint_filters_category() -> None:
    response = make_client().get("/api/v1/reconciliation", params={"category": "MISSING_FOLDER"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["category"] == "MISSING_FOLDER"


def test_reports_summary_endpoint() -> None:
    response = make_client().get("/api/v1/reports/summary")

    payload = response.json()
    assert response.status_code == 200
    assert payload["summary"]["project_status"]["IN_PROGRESS"] == 1
    assert payload["summary"]["reconciliation_category"]["MATCHED"] == 1
