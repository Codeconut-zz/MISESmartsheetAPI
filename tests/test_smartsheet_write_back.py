import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from typer.testing import CliRunner

from app.cli import main as cli
from app.cli.main import app
from app.config import Settings, SmartsheetSettings, get_settings
from app.connectors.smartsheet_client import (
    SmartsheetClient,
    SmartsheetSafetyError,
    SmartsheetWriteSafetyContext,
)
from app.domain.plan import OperationRiskLevel, OperationType, Plan, PlanOperation
from app.services.audit_service import AuditService, InMemoryAuditSink
from app.services.dry_run_planner import export_plan
from app.services.smartsheet_write_back_service import (
    SmartsheetWriteBackError,
    SmartsheetWriteBackService,
)

BASE_URL = "https://api.smartsheet.test/2.0"
TOKEN = "test-token-value"
runner = CliRunner()


class FakeWriteClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __enter__(self) -> "FakeWriteClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def update_row_cells(
        self,
        sheet_id: str,
        row_id: str,
        cells: list[dict[str, Any]],
        *,
        safety_context: SmartsheetWriteSafetyContext,
    ) -> dict[str, Any]:
        safety_context.require_approved()
        self.calls.append({"sheet_id": sheet_id, "row_id": row_id, "cells": cells})
        return {"message": "SUCCESS"}


def write_settings() -> Settings:
    return Settings(environment="test", enable_write_operations=True, _env_file=None)


def make_context(*, operation_id: str = "op-write-1") -> SmartsheetWriteSafetyContext:
    return SmartsheetWriteSafetyContext(
        dry_run_completed=True,
        enable_write_operations=True,
        apply_requested=True,
        operation_id=operation_id,
        approved_operation_ids=frozenset({operation_id}),
        plan_path="plan.json",
    )


def make_write_operation(
    *,
    operation_id: str = "op-write-1",
    field: str = "Project Folder Link",
    value: str = "C:/MISE/ABED/MISE-ABED-001",
) -> PlanOperation:
    return PlanOperation(
        operation_id=operation_id,
        operation_type=OperationType.UPDATE_SMARTSHEET_ROW,
        target="sheet_id:sheet-123,row_id:row-456",
        reason="Update project metadata in Smartsheet",
        before_state={"sheet_id": "sheet-123", "row_id": "row-456"},
        after_state={
            "sheet_id": "sheet-123",
            "row_id": "row-456",
            "cells": [
                {"columnId": 2001, "field": field, "value": value},
                {"columnId": 2002, "field": "Reconciliation Status", "value": "MATCHED"},
                {"columnId": 2003, "field": "Integration Last Sync"},
            ],
        },
        risk_level=OperationRiskLevel.HIGH,
        dry_run_result="Would update allowed Smartsheet write-back columns",
    )


def make_plan(*operations: PlanOperation) -> Plan:
    return Plan(
        blueprint_path="config/architecture/mise_ministry_blueprint.example.yaml",
        operation_count=len(operations),
        operations=list(operations),
    )


def write_plan(tmp_path: Path, plan: Plan) -> Path:
    plan_path = tmp_path / "plan.json"
    export_plan(plan, plan_path)
    return plan_path


@respx.mock
def test_client_update_row_cells_requires_safety_context_and_puts_cells() -> None:
    route = respx.put(f"{BASE_URL}/sheets/sheet-123/rows").mock(
        return_value=httpx.Response(200, json={"message": "SUCCESS"})
    )
    client = SmartsheetClient(
        settings=SmartsheetSettings(
            base_url=BASE_URL,
            access_token=TOKEN,
            tir_sheet_id="sheet-123",
        ),
        retry_attempts=1,
    )

    with client:
        response = client.update_row_cells(
            "sheet-123",
            "row-456",
            [{"columnId": 2001, "value": "C:/MISE/project"}],
            safety_context=make_context(),
        )

    payload = json.loads(route.calls[0].request.content)
    assert response == {"message": "SUCCESS"}
    assert payload == [{"id": "row-456", "cells": [{"columnId": 2001, "value": "C:/MISE/project"}]}]


def test_client_update_row_cells_rejects_unapproved_operation() -> None:
    context = SmartsheetWriteSafetyContext(
        dry_run_completed=True,
        enable_write_operations=True,
        apply_requested=True,
        operation_id="op-rogue",
        approved_operation_ids=frozenset({"op-approved"}),
        plan_path="plan.json",
    )
    client = SmartsheetClient(
        settings=SmartsheetSettings(base_url=BASE_URL, access_token=TOKEN, tir_sheet_id="sheet-123")
    )

    with client, pytest.raises(SmartsheetSafetyError, match="approved_plan_operation"):
        client.update_row_cells(
            "sheet-123",
            "row-456",
            [{"columnId": 2001, "value": "C:/MISE/project"}],
            safety_context=context,
        )


def test_write_back_service_requires_write_flag(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_write_operation()))
    service = SmartsheetWriteBackService(
        smartsheet_client=FakeWriteClient(),
        settings=Settings(environment="test", enable_write_operations=False, _env_file=None),
    )

    with pytest.raises(SmartsheetWriteBackError, match="ENABLE_WRITE_OPERATIONS"):
        service.apply_plan(plan_path=plan_path, apply=True)


def test_write_back_service_requires_apply_flag(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_write_operation()))
    service = SmartsheetWriteBackService(
        smartsheet_client=FakeWriteClient(),
        settings=write_settings(),
    )

    with pytest.raises(SmartsheetWriteBackError, match="--apply"):
        service.apply_plan(plan_path=plan_path, apply=False)


@pytest.mark.parametrize("protected_field", ["SECRETARY APPROVAL", "CONTACT EMAIL"])
def test_write_back_service_rejects_protected_fields(tmp_path: Path, protected_field: str) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_write_operation(field=protected_field)))
    client = FakeWriteClient()
    service = SmartsheetWriteBackService(smartsheet_client=client, settings=write_settings())

    with pytest.raises(SmartsheetWriteBackError, match="Protected Smartsheet field"):
        service.apply_plan(plan_path=plan_path, apply=True)

    assert client.calls == []


def test_write_back_service_updates_allowed_cells_and_audits(tmp_path: Path) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_write_operation()))
    sink = InMemoryAuditSink()
    client = FakeWriteClient()
    service = SmartsheetWriteBackService(
        smartsheet_client=client,
        settings=write_settings(),
        audit=AuditService(sink=sink),
    )

    result = service.apply_plan(plan_path=plan_path, apply=True, actor="tester")

    assert result.updated_count == 1
    assert client.calls[0]["sheet_id"] == "sheet-123"
    assert client.calls[0]["row_id"] == "row-456"
    assert client.calls[0]["cells"][0] == {"columnId": 2001, "value": "C:/MISE/ABED/MISE-ABED-001"}
    assert client.calls[0]["cells"][2]["value"]
    assert [event.status for event in sink.list_events()] == ["pending", "success"]


def test_apply_smartsheet_plan_cli_uses_approved_plan(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    plan_path = write_plan(tmp_path, make_plan(make_write_operation()))
    client = FakeWriteClient()
    monkeypatch.setenv("ENABLE_WRITE_OPERATIONS", "true")
    monkeypatch.setattr(cli, "get_smartsheet_client", lambda: client)
    get_settings.cache_clear()

    result = runner.invoke(app, ["apply-smartsheet-plan", str(plan_path), "--apply"])

    get_settings.cache_clear()
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["updated_count"] == 1
    assert client.calls[0]["sheet_id"] == "sheet-123"
