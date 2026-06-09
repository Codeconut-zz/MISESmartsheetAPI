"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="MISE Smartsheet Integration Service")


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "ok"}
