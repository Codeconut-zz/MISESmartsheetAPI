import json
from pathlib import Path

import pytest

from app.domain.tir import TechnicalIntakeRequest
from app.services.tir_mapper import TIRMapper, TIRMappingError, load_tir_column_map

FIXTURE_PATH = Path("tests/fixtures/tir_rows.json")


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_tir_column_map_uses_exact_display_names() -> None:
    column_map = load_tir_column_map()

    assert column_map["SECRETARY APPROVAL"] == "secretary_approval"
    assert column_map["REGISTRY (MISE File Ref)"] == "registry_file_ref"
    assert column_map["PROJECT NAME (Subject)"] == "project_name"


def test_mapper_converts_smartsheet_row_to_tir_model() -> None:
    fixture = load_fixture()
    mapper = TIRMapper()

    tir = mapper.map_row(row=fixture["rows"][0], columns=fixture["columns"])

    assert isinstance(tir, TechnicalIntakeRequest)
    assert tir.secretary_approval is True
    assert tir.registry_confirmation is True
    assert tir.project_status == "IN_PROGRESS"
    assert tir.contact_number == "+686 00000"
    assert "Inspection\nCost estimate" in tir.service_request


def test_mapper_rejects_missing_columns() -> None:
    fixture = load_fixture()
    columns = [
        column for column in fixture["columns"] if column["title"] != "CONTACT EMAIL"
    ]

    with pytest.raises(TIRMappingError, match="CONTACT EMAIL"):
        TIRMapper().map_row(row=fixture["rows"][0], columns=columns)


def test_tir_model_rejects_unknown_status() -> None:
    fixture = load_fixture()
    row = json.loads(json.dumps(fixture["rows"][0]))
    status_cell = next(cell for cell in row["cells"] if cell["columnId"] == 11)
    status_cell["value"] = "waiting for magic"

    with pytest.raises(TIRMappingError, match="Unknown project status"):
        TIRMapper().map_row(row=row, columns=fixture["columns"])


def test_tir_model_rejects_invalid_email() -> None:
    fixture = load_fixture()
    row = json.loads(json.dumps(fixture["rows"][0]))
    email_cell = next(cell for cell in row["cells"] if cell["columnId"] == 15)
    email_cell["value"] = "not-an-email"

    with pytest.raises(TIRMappingError, match="valid email"):
        TIRMapper().map_row(row=row, columns=fixture["columns"])


def test_tir_model_rejects_integer_phone() -> None:
    fixture = load_fixture()
    row = json.loads(json.dumps(fixture["rows"][0]))
    phone_cell = next(cell for cell in row["cells"] if cell["columnId"] == 14)
    phone_cell["value"] = 12345

    with pytest.raises(TIRMappingError, match="must be a string"):
        TIRMapper().map_row(row=row, columns=fixture["columns"])
