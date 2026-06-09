import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from app.cli.main import app
from app.connectors.mise_filesystem import MISEFilesystem, infer_registry_file_ref
from app.services.filesystem_discovery_service import FilesystemDiscoveryService

runner = CliRunner()


def create_tree(root: Path) -> None:
    (root / "MISE-ABED-001 - Community hall roof repair").mkdir()
    (root / "MISE-ABED-001 - Community hall roof repair" / "scope.txt").write_text(
        "inspect roof",
        encoding="utf-8",
    )
    (root / "MISE-CED-002 - Road drainage" / "nested").mkdir(parents=True)
    (root / "MISE-CED-002 - Road drainage" / "nested" / "deep").mkdir()


def test_filesystem_scanner_is_read_only_and_extracts_inventory(tmp_path: Path) -> None:
    create_tree(tmp_path)

    inventory = MISEFilesystem().scan(tmp_path, max_depth=2)

    names = {entry.folder_name for entry in inventory}
    project = next(
        entry for entry in inventory if entry.folder_name.startswith("MISE-ABED-001")
    )
    assert "MISE-ABED-001 - Community hall roof repair" in names
    assert "nested" in names
    assert "deep" not in names
    assert project.inferred_registry_file_ref == "MISE-ABED-001"
    assert project.inferred_project_name == "Community hall roof repair"
    assert project.file_count == 1


def test_registry_reference_inference_is_conservative() -> None:
    assert infer_registry_file_ref("MISE_ABED_001 - Project") == "MISE-ABED-001"
    assert infer_registry_file_ref("No reference here") is None


def test_discovery_service_exports_json_and_csv(tmp_path: Path) -> None:
    create_tree(tmp_path)
    json_path = tmp_path / "exports" / "inventory.json"
    csv_path = tmp_path / "exports" / "inventory.csv"
    service = FilesystemDiscoveryService()

    json_result = service.scan(root=tmp_path, max_depth=1, out=json_path, pretty=True)
    service.scan(root=tmp_path, max_depth=1, out=csv_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert payload["summary"]["folders_scanned"] == json_result.summary.folders_scanned
    assert rows
    assert "folder_path" in rows[0]


def test_filesystem_cli_scan_outputs_summary(tmp_path: Path) -> None:
    create_tree(tmp_path)
    output_path = tmp_path / "folder_inventory.json"

    result = runner.invoke(
        app,
        ["filesystem", "scan", "--root", str(tmp_path), "--max-depth", "1", "--out", str(output_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["folders_scanned"] >= 3
    assert output_path.exists()
