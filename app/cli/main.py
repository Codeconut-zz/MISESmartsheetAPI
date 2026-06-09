"""Typer command-line entry point."""

import typer

app = typer.Typer(help="MISE Smartsheet Integration CLI.")


@app.command()
def health() -> None:
    """Print a simple health message."""
    typer.echo("ok")


if __name__ == "__main__":
    app()
