"""Typer command-line entry point."""

import json
from typing import Any

import typer

from app.config import get_settings
from app.connectors.smartsheet_client import SmartsheetClient, SmartsheetError
from app.services.organization_loader import BlueprintLoadError, load_organization_blueprint
from app.services.organization_loader import summarize_blueprint

app = typer.Typer(name="mise-smartsheet", help="MISE Smartsheet Integration CLI.")
smartsheet_app = typer.Typer(help="Read-only Smartsheet commands.")
org_app = typer.Typer(help="MISE organization blueprint commands.")
tir_app = typer.Typer(help="TIR workflow commands.")
filesystem_app = typer.Typer(help="Filesystem discovery commands.")
reconcile_app = typer.Typer(help="Reconciliation commands.")
report_app = typer.Typer(help="Reporting commands.")
plan_app = typer.Typer(help="Dry-run planning commands.")
apply_app = typer.Typer(help="Guarded apply commands.")

app.add_typer(smartsheet_app, name="smartsheet")
app.add_typer(org_app, name="org")
app.add_typer(tir_app, name="tir")
app.add_typer(filesystem_app, name="filesystem")
app.add_typer(reconcile_app, name="reconcile")
app.add_typer(report_app, name="report")
app.add_typer(plan_app, name="plan")
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
