"""Typer command-line entry point."""

import json
from pathlib import Path
import time
from typing import Any

import typer

from app.config import get_settings
from app.connectors.smartsheet_client import SmartsheetClient, SmartsheetError
from app.services.organization_loader import BlueprintLoadError, load_organization_blueprint
from app.services.organization_loader import summarize_blueprint
from app.services.audit_service import AuditService, InMemoryAuditSink
from app.services.filesystem_discovery_service import FilesystemDiscoveryService
from app.services.data_quality_service import DataQualityService, export_data_quality_report
from app.services.dry_run_planner import DryRunPlanner, export_plan
from app.services.polling_service import PollingError, PollingService
from app.services.project_folder_creation_service import (
    ProjectFolderCreationError,
    ProjectFolderCreationService,
)
from app.services.reconciliation_service import ReconciliationService
from app.services.reconciliation_service import export_reconciliation_results
from app.services.reconciliation_service import load_folder_inventory_export, load_tir_records_export
from app.services.report_export_service import ReportExportService
from app.services.tir_pull_service import TIRPullError, TIRPullService
from app.connectors.mise_filesystem import FilesystemScanError
from app.storage.database import get_engine, session_scope
from app.storage.models import Base

app = typer.Typer(name="mise-smartsheet", help="MISE Smartsheet Integration CLI.")
smartsheet_app = typer.Typer(help="Read-only Smartsheet commands.")
org_app = typer.Typer(help="MISE organization blueprint commands.")
db_app = typer.Typer(help="Database migration commands.")
tir_app = typer.Typer(help="TIR workflow commands.")
filesystem_app = typer.Typer(help="Filesystem discovery commands.")
reconcile_app = typer.Typer(help="Reconciliation commands.")
report_app = typer.Typer(help="Reporting commands.")
data_quality_app = typer.Typer(help="Data quality commands.")
sync_app = typer.Typer(help="Read-only synchronization commands.")
apply_app = typer.Typer(help="Guarded apply commands.")

app.add_typer(smartsheet_app, name="smartsheet")
app.add_typer(org_app, name="org")
app.add_typer(db_app, name="db")
app.add_typer(tir_app, name="tir")
app.add_typer(filesystem_app, name="filesystem")
app.add_typer(reconcile_app, name="reconcile")
app.add_typer(report_app, name="report")
app.add_typer(data_quality_app, name="data-quality")
app.add_typer(sync_app, name="sync")
app.add_typer(apply_app, name="apply")


@app.command()
def health(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Print service health."""
    _echo_json({"status": "ok"}, pretty=pretty)


@smartsheet_app.command("whoami")
def smartsheet_whoami(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Return the current Smartsheet user."""
    _run_smartsheet_command(lambda client: client.whoami(), pretty=pretty)


@smartsheet_app.command("list-workspaces")
def smartsheet_list_workspaces(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """List Smartsheet workspaces."""
    _run_smartsheet_command(
        lambda client: {"data": client.list_workspaces()},
        pretty=pretty,
    )


@smartsheet_app.command("list-sheets")
def smartsheet_list_sheets(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """List Smartsheet sheets."""
    _run_smartsheet_command(
        lambda client: {"data": client.list_sheets()},
        pretty=pretty,
    )


@org_app.command("validate-blueprint")
def org_validate_blueprint(
    path: str = typer.Argument(..., help="Path to a MISE organization blueprint YAML file."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Validate a MISE organization blueprint file."""
    try:
        blueprint = load_organization_blueprint(path)
    except BlueprintLoadError as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json({"status": "valid", "blueprint": summarize_blueprint(blueprint)}, pretty=pretty)


@db_app.command("init")
def db_init(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Create database tables for local development."""
    try:
        Base.metadata.create_all(get_engine())
    except Exception as exc:
        _echo_error(f"Database initialization failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json({"status": "initialized"}, pretty=pretty)


@db_app.command("upgrade")
def db_upgrade(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Run Alembic migrations to head."""
    try:
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config("alembic.ini"), "head")
    except Exception as exc:
        _echo_error(f"Database upgrade failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json({"status": "upgraded"}, pretty=pretty)


@db_app.command("status")
def db_status(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Report current database connectivity and table count."""
    try:
        engine = get_engine()
        table_count = len(Base.metadata.tables)
        dialect = engine.dialect.name
    except Exception as exc:
        _echo_error(f"Database status failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json({"status": "configured", "dialect": dialect, "table_count": table_count}, pretty=pretty)


@tir_app.command("pull")
def tir_pull(
    sheet_id: str | None = typer.Option(None, "--sheet-id", help="Override SMARTSHEET_TIR_SHEET_ID."),
    out: Path | None = typer.Option(None, "--out", help="Write raw and normalized JSON export."),
    persist: bool = typer.Option(False, "--persist", help="Persist valid records to the database."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Pull and validate TIR rows from Smartsheet."""
    effective_sheet_id = sheet_id or get_settings().smartsheet.tir_sheet_id
    if not effective_sheet_id:
        _echo_error("SMARTSHEET_TIR_SHEET_ID is required unless --sheet-id is provided", pretty=pretty)
        raise typer.Exit(code=1)

    try:
        with get_smartsheet_client() as client:
            service = TIRPullService(
                smartsheet_client=client,
                session_scope_factory=lambda: session_scope(),
            )
            result = service.pull(
                sheet_id=effective_sheet_id,
                persist=persist,
                out=out,
                pretty=pretty,
            )
    except (TIRPullError, SmartsheetError, typer.BadParameter) as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(result.summary.model_dump(mode="json"), pretty=pretty)


@filesystem_app.command("scan")
def filesystem_scan(
    root: Path | None = typer.Option(None, "--root", help="Root folder to scan."),
    max_depth: int = typer.Option(4, "--max-depth", min=0, help="Maximum recursive folder depth."),
    out: Path | None = typer.Option(None, "--out", help="Write JSON or CSV inventory export."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Scan MISE folders without modifying files."""
    try:
        result = FilesystemDiscoveryService().scan(
            root=root,
            max_depth=max_depth,
            out=out,
            pretty=pretty,
        )
    except FilesystemScanError as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(result.summary.model_dump(mode="json"), pretty=pretty)


@reconcile_app.callback(invoke_without_command=True)
def reconcile(
    ctx: typer.Context,
    tir: Path | None = typer.Option(None, "--tir", help="TIR pull JSON export."),
    folders: Path | None = typer.Option(None, "--folders", help="Folder inventory JSON export."),
    out: Path | None = typer.Option(None, "--out", help="Write XLSX, CSV, or JSON results."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Reconcile TIR records with discovered folders."""
    if ctx.invoked_subcommand is not None:
        return
    if tir is None or folders is None:
        _echo_error("--tir and --folders are required", pretty=pretty)
        raise typer.Exit(code=1)

    try:
        results = ReconciliationService().reconcile(
            tir_records=load_tir_records_export(tir),
            folder_inventory=load_folder_inventory_export(folders),
        )
        if out is not None:
            export_reconciliation_results(results, out)
    except Exception as exc:
        _echo_error(f"Reconciliation failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    category_counts: dict[str, int] = {}
    for result in results:
        category_counts[result.category] = category_counts.get(result.category, 0) + 1

    _echo_json({"results": len(results), "category_counts": category_counts}, pretty=pretty)


@report_app.command("export")
def report_export(
    tir: Path = typer.Option(..., "--tir", help="TIR pull JSON export."),
    folders: Path = typer.Option(..., "--folders", help="Folder inventory JSON export."),
    reconciliation: Path = typer.Option(..., "--reconciliation", help="Reconciliation export."),
    out: Path = typer.Option(Path("data/reports"), "--out", help="Output report directory."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Generate JSON, CSV, and Excel reporting outputs."""
    try:
        result = ReportExportService().export(
            tir_path=tir,
            folders_path=folders,
            reconciliation_path=reconciliation,
            out_dir=out,
        )
    except Exception as exc:
        _echo_error(f"Report export failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(result.model_dump(mode="json"), pretty=pretty)


@data_quality_app.command("check")
def data_quality_check(
    tir: Path = typer.Option(..., "--tir", help="TIR pull JSON export."),
    out: Path | None = typer.Option(None, "--out", help="Write XLSX, CSV, or JSON issues."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Check TIR records for data-quality issues."""
    try:
        report = DataQualityService().check(load_tir_records_export(tir))
        if out is not None:
            export_data_quality_report(report, out)
    except Exception as exc:
        _echo_error(f"Data quality check failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(report.summary.model_dump(mode="json"), pretty=pretty)


@sync_app.command("poll-once")
def sync_poll_once(
    sheet_id: str | None = typer.Option(None, "--sheet-id", help="Override SMARTSHEET_TIR_SHEET_ID."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Run one read-only polling cycle."""
    try:
        with get_smartsheet_client() as client:
            result = PollingService(
                smartsheet_client=client,
                session_scope_factory=lambda: session_scope(),
            ).poll_once(sheet_id=sheet_id)
    except (PollingError, SmartsheetError, typer.BadParameter) as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(result.model_dump(mode="json"), pretty=pretty)


@sync_app.command("poll")
def sync_poll(
    interval_seconds: int = typer.Option(300, "--interval-seconds", min=1),
    sheet_id: str | None = typer.Option(None, "--sheet-id", help="Override SMARTSHEET_TIR_SHEET_ID."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Run a development polling loop until interrupted."""
    while True:
        sync_poll_once(sheet_id=sheet_id, pretty=pretty)
        time.sleep(interval_seconds)


@app.command("plan")
def plan(
    blueprint_path: Path = typer.Argument(..., help="Path to a MISE organization blueprint YAML file."),
    out: Path = typer.Option(Path("data/reports/plan.json"), "--out", help="Write plan JSON output."),
    tir: Path | None = typer.Option(None, "--tir", help="Optional TIR pull JSON export."),
    folders: Path | None = typer.Option(None, "--folders", help="Optional folder inventory JSON export."),
    reconciliation: Path | None = typer.Option(None, "--reconciliation", help="Optional reconciliation export."),
    report_root: Path = typer.Option(Path("data/reports"), "--report-root", help="Report folder root."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Build a dry-run plan without changing external systems."""
    try:
        dry_run_plan = DryRunPlanner().build_plan(
            blueprint_path=blueprint_path,
            report_root=report_root,
            tir_path=tir,
            folders_path=folders,
            reconciliation_path=reconciliation,
        )
        export_plan(dry_run_plan, out, pretty=True)
    except Exception as exc:
        _echo_error(f"Dry-run planning failed: {exc}", pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(
        {
            "status": "planned",
            "plan_path": str(out),
            "operation_count": dry_run_plan.operation_count,
            "warnings": dry_run_plan.warnings,
        },
        pretty=pretty,
    )


@app.command("apply-folder-plan")
def apply_folder_plan(
    plan_path: Path = typer.Argument(..., help="Previously generated dry-run plan JSON file."),
    apply: bool = typer.Option(False, "--apply", help="Actually create folders from the plan."),
    root: Path | None = typer.Option(None, "--root", help="Override MISE_PROJECT_ROOT for folder creation."),
    actor: str = typer.Option("system", "--actor", help="Audit actor recorded for created folders."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty-print JSON output."),
) -> None:
    """Create project folders from an approved dry-run plan."""
    try:
        result = ProjectFolderCreationService(
            audit=AuditService(sink=InMemoryAuditSink(), emit_logs=False)
        ).apply_plan(
            plan_path=plan_path,
            apply=apply,
            project_root=root,
            actor=actor,
        )
    except ProjectFolderCreationError as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc

    _echo_json(result.model_dump(mode="json"), pretty=pretty)


def get_smartsheet_client() -> SmartsheetClient:
    """Create a configured Smartsheet client for CLI commands."""
    smartsheet_settings = get_settings().smartsheet
    if not smartsheet_settings.access_token:
        raise typer.BadParameter(
            "SMARTSHEET_ACCESS_TOKEN is required for Smartsheet CLI commands."
        )

    return SmartsheetClient(settings=smartsheet_settings)


def _run_smartsheet_command(
    command: Any,
    *,
    pretty: bool,
) -> None:
    try:
        with get_smartsheet_client() as client:
            _echo_json(command(client), pretty=pretty)
    except typer.BadParameter as exc:
        _echo_error(str(exc), pretty=pretty)
        raise typer.Exit(code=1) from exc
    except SmartsheetError as exc:
        message = _smartsheet_error_message(exc)
        _echo_error(message, pretty=pretty, status_code=exc.status_code)
        raise typer.Exit(code=1) from exc


def _smartsheet_error_message(exc: SmartsheetError) -> str:
    if exc.status_code in {401, 403}:
        return "Smartsheet authentication failed. Check SMARTSHEET_ACCESS_TOKEN permissions."

    return str(exc)


def _echo_json(payload: Any, *, pretty: bool) -> None:
    typer.echo(_to_json(payload, pretty=pretty))


def _echo_error(message: str, *, pretty: bool, status_code: int | None = None) -> None:
    payload: dict[str, Any] = {"error": message}
    if status_code is not None:
        payload["status_code"] = status_code
    typer.echo(_to_json(payload, pretty=pretty), err=True)


def _to_json(payload: Any, *, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, indent=2, sort_keys=True)

    return json.dumps(payload, separators=(",", ":"))


if __name__ == "__main__":
    app()
