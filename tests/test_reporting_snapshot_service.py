from collections.abc import Callable, Iterator
from datetime import UTC, datetime

from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_db_session
from app.domain.tir import TechnicalIntakeRequest
from app.main import app
from app.security.auth import AuthenticatedUser, get_current_user
from app.services.reconciliation_service import ReconciliationResult
from app.services.reporting_snapshot_service import ReportingSnapshotService
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import Base
from app.storage.repositories import ReportingRepository


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


def auth_override() -> AuthenticatedUser:
    return AuthenticatedUser(subject="test-user", roles={"admin"})


def make_tir(
    *,
    registry_file_ref: str,
    project_name: str,
    department: str,
    status: str,
    secretary_approval: bool,
    service_request: str,
    funding_source: str = "Government",
) -> TechnicalIntakeRequest:
    return TechnicalIntakeRequest(
        created=datetime(2026, 6, 1, tzinfo=UTC),
        secretary_approval=secretary_approval,
        mise_hod=department,
        registry_confirmation=True,
        registry_file_ref=registry_file_ref,
        organisation="MISE",
        project_name=project_name,
        service_request=service_request,
        project_location="Tarawa",
        project_status=status,
        contact_person="Example Contact",
        contact_email=f"{registry_file_ref.lower()}@example.test",
        funding_source=funding_source,
    )


def sample_tir_records() -> list[TechnicalIntakeRequest]:
    return [
        make_tir(
            registry_file_ref="MISE-ABED-001",
            project_name="Clinic concept design",
            department="ABED",
            status="APPROVED",
            secretary_approval=True,
            service_request="ADD architectural design",
        ),
        make_tir(
            registry_file_ref="MISE-ABED-002",
            project_name="Cost plan review",
            department="ABED",
            status="PENDING",
            secretary_approval=False,
            service_request="CPD cost planning",
            funding_source="",
        ),
        make_tir(
            registry_file_ref="MISE-CED-003",
            project_name="Road drainage",
            department="CED",
            status="DECLINED",
            secretary_approval=False,
            service_request="Civil inspection",
        ),
        make_tir(
            registry_file_ref="MISE-EPD-004",
            project_name="Solar audit",
            department="EPD",
            status="IN_PROGRESS",
            secretary_approval=True,
            service_request="Energy planning",
        ),
        make_tir(
            registry_file_ref="MISE-WSED-005",
            project_name="Pump replacement",
            department="WSED",
            status="COMPLETED",
            secretary_approval=True,
            service_request="Water engineering",
        ),
    ]


def sample_reconciliation() -> list[ReconciliationResult]:
    return [
        ReconciliationResult(
            registry_file_ref="MISE-CED-003",
            project_name="Road drainage",
            contact_email="ced@example.test",
            category="MISSING_FOLDER",
            confidence_score=0,
            reasons=["No folder matched registry reference or project name"],
        )
    ]


def test_reporting_snapshot_service_generates_required_views() -> None:
    snapshots = ReportingSnapshotService().generate(
        tir_records=sample_tir_records(),
        reconciliation_results=sample_reconciliation(),
    )
    by_name = {snapshot.snapshot_name: snapshot for snapshot in snapshots}

    assert len(snapshots) == 11
    assert by_name["Ministry-wide portfolio"].project_count == 5
    assert by_name["Ministry-wide portfolio"].declined_projects == 1
    assert by_name["Ministry-wide portfolio"].missing_folder_count == 1
    assert by_name["ABED view"].project_count == 2
    assert by_name["ABED view"].pending_approvals == 1
    assert by_name["ABED ADD view"].project_count == 1
    assert by_name["ABED CPD view"].missing_data_count == 1


def test_reporting_snapshot_service_persists_snapshots() -> None:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ReportingSnapshotService(session_scope_factory=lambda: session_scope(engine))
    snapshots = service.generate(
        tir_records=sample_tir_records(),
        reconciliation_results=sample_reconciliation(),
    )

    service.persist(snapshots)

    with session_scope(engine) as session:
        stored = ReportingRepository().list_department_snapshots(session)

    assert len(stored) == 11
    assert any(
        snapshot.snapshot_name == "Director General technical delivery view"
        for snapshot in stored
    )


def make_session_override() -> Callable[[], Iterator[object]]:
    engine = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    service = ReportingSnapshotService(session_scope_factory=lambda: session_scope(engine))
    service.persist(
        service.generate(
            tir_records=sample_tir_records(),
            reconciliation_results=sample_reconciliation(),
        )
    )

    def override() -> Iterator[object]:
        with session_scope(engine) as session:
            yield session

    return override


def test_department_snapshots_api_endpoint() -> None:
    app.dependency_overrides[get_db_session] = make_session_override()
    app.dependency_overrides[get_current_user] = auth_override
    client = TestClient(app)

    response = client.get("/api/v1/reports/department-snapshots")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 11
    assert any(item["snapshot_name"] == "ABED view" for item in payload["items"])
