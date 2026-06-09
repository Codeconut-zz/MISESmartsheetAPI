import json
from pathlib import Path

from sqlalchemy import inspect

from app.services.tir_mapper import TIRMapper
from app.storage.database import create_engine_from_url, session_scope
from app.storage.models import (
    AuditEventRecord,
    Base,
    DepartmentReportingSnapshot,
    ProjectFolderInventory,
    ReconciliationResult,
    TIRRecord,
)
from app.storage.repositories import TIRRecordRepository

FIXTURE_PATH = Path("tests/fixtures/tir_rows.json")


def make_sqlite_engine():
    return create_engine_from_url("sqlite:///:memory:")


def test_database_models_create_required_tables() -> None:
    engine = make_sqlite_engine()

    Base.metadata.create_all(engine)

    table_names = set(inspect(engine).get_table_names())
    assert {
        TIRRecord.__tablename__,
        ProjectFolderInventory.__tablename__,
        ReconciliationResult.__tablename__,
        AuditEventRecord.__tablename__,
        DepartmentReportingSnapshot.__tablename__,
    }.issubset(table_names)


def test_database_models_include_required_indexes() -> None:
    engine = make_sqlite_engine()

    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    tir_index_names = {index["name"] for index in inspector.get_indexes("tir_records")}
    reporting_index_names = {
        index["name"] for index in inspector.get_indexes("department_reporting_snapshots")
    }

    assert "ix_tir_records_registry_file_ref" in tir_index_names
    assert "ix_tir_records_project_name" in tir_index_names
    assert "ix_tir_records_contact_email" in tir_index_names
    assert "ix_tir_records_project_status" in tir_index_names
    assert "ix_tir_records_funding_source" in tir_index_names
    assert "ix_department_reporting_snapshots_department_code" in reporting_index_names
    assert "ix_department_reporting_snapshots_funding_source" in reporting_index_names


def test_tir_repository_persists_tir_record_with_sqlite() -> None:
    engine = make_sqlite_engine()
    Base.metadata.create_all(engine)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    tir = TIRMapper().map_row(row=fixture["rows"][0], columns=fixture["columns"])
    repository = TIRRecordRepository()

    with session_scope(engine) as session:
        record = repository.add(
            session,
            tir,
            smartsheet_sheet_id="sheet-123",
            smartsheet_row_id="row-456",
        )
        record_id = record.id

    with session_scope(engine) as session:
        stored = repository.get_by_registry_file_ref(session, "MISE-ABED-001")

        assert stored is not None
        assert stored.id == record_id
        assert stored.smartsheet_sheet_id == "sheet-123"
        assert stored.smartsheet_row_id == "row-456"
        assert stored.project_name == "Community hall roof repair"
