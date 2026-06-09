from datetime import UTC, datetime
import json
from pathlib import Path

from typer.testing import CliRunner

from app.cli.main import app
from app.connectors.mise_filesystem import FolderInventoryEntry
from app.domain.tir import TechnicalIntakeRequest
from app.services.reconciliation_service import (
    ReconciliationService,
    export_reconciliation_results,
)

runner = CliRunner()


def make_tir(
    *,
    registry_file_ref: str = "MISE-ABED-001",
    project_name: str = "Community hall roof repair",
    contact_email: str = "contact@example.test",
) -> TechnicalIntakeRequest:
    return TechnicalIntakeRequest(
        created=datetime(2026, 6, 1, tzinfo=UTC),
        secretary_approval=True,
        mise_hod="ABED",
        registry_confirmation=True,
        registry_file_ref=registry_file_ref,
        organisation="Betio Town Council",
        project_name=project_name,
        service_request="Inspection",
        project_location="Betio",
        project_status="IN_PROGRESS",
        contact_person="Example Contact",
        contact_email=contact_email,
    )


def make_folder(
    *,
    registry_file_ref: str | None = "MISE-ABED-001",
    project_name: str | None = "Community hall roof repair",
    path: str = "C:/MISE/MISE-ABED-001 - Community hall roof repair",
) -> FolderInventoryEntry:
    return FolderInventoryEntry(
        folder_path=path,
        folder_name=Path(path).name,
        parent_path=str(Path(path).parent),
        modified_time=datetime(2026, 6, 1, tzinfo=UTC),
        inferred_registry_file_ref=registry_file_ref,
        inferred_project_name=project_name,
        file_count=2,
    )


def test_reconciliation_exact_registry_match() -> None:
    result = ReconciliationService().reconcile(
        tir_records=[make_tir()],
        folder_inventory=[make_folder()],
    )[0]

    assert result.category == "MATCHED"
    assert result.confidence_score == 100
    assert "Exact registry reference match" in result.reasons[0]


def test_reconciliation_duplicate_registry_reference() -> None:
    result = ReconciliationService().reconcile(
        tir_records=[make_tir()],
        folder_inventory=[
            make_folder(path="C:/MISE/MISE-ABED-001 - A"),
            make_folder(path="C:/MISE/MISE-ABED-001 - B"),
        ],
    )[0]

    assert result.category == "DUPLICATE_REGISTRY_REFERENCE"
    assert result.confidence_score == 80


def test_reconciliation_missing_registry_reference() -> None:
    result = ReconciliationService().reconcile(
        tir_records=[make_tir(registry_file_ref="")],
        folder_inventory=[make_folder()],
    )[0]

    assert result.category == "MISSING_REGISTRY_REFERENCE"
    assert result.confidence_score == 0


def test_reconciliation_missing_folder() -> None:
    result = ReconciliationService().reconcile(
        tir_records=[make_tir(registry_file_ref="MISE-WSED-999", project_name="No folder project")],
        folder_inventory=[make_folder()],
    )[0]

    assert result.category == "MISSING_FOLDER"
    assert result.matched_folder_path is None


def test_reconciliation_possible_match() -> None:
    result = ReconciliationService().reconcile(
        tir_records=[
            make_tir(
                registry_file_ref="MISE-ABED-999",
                project_name="Community hall roofing repairs",
            )
        ],
        folder_inventory=[make_folder()],
    )[0]

    assert result.category == "POSSIBLE_MATCH"
    assert result.confidence_score >= 70
    assert result.matched_folder_path is not None


def test_reconciliation_cli_exports_xlsx(tmp_path: Path) -> None:
    tir_path = tmp_path / "tir_rows.json"
    folders_path = tmp_path / "folder_inventory.json"
    output_path = tmp_path / "reconciliation.xlsx"
    tir_path.write_text(
        json.dumps({"normalized": [make_tir().model_dump(mode="json")]}),
        encoding="utf-8",
    )
    folders_path.write_text(
        json.dumps({"inventory": [make_folder().model_dump(mode="json")]}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "--tir",
            str(tir_path),
            "--folders",
            str(folders_path),
            "--out",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["category_counts"] == {"MATCHED": 1}
    assert output_path.exists()


def test_reconciliation_export_json(tmp_path: Path) -> None:
    output_path = tmp_path / "reconciliation.json"
    result = ReconciliationService().reconcile(
        tir_records=[make_tir()],
        folder_inventory=[make_folder()],
    )

    export_reconciliation_results(result, output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload[0]["category"] == "MATCHED"
