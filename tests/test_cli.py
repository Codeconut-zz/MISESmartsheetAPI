from typer.main import Typer

from app.cli.main import app


def test_cli_app_imports() -> None:
    assert isinstance(app, Typer)
