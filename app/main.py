"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.reconciliation import router as reconciliation_router
from app.api.reports import router as reports_router
from app.api.tir import router as tir_router
from app.api.webhooks import router as webhooks_router

app = FastAPI(title="MISE Smartsheet Integration Service")

app.include_router(health_router)
app.include_router(tir_router)
app.include_router(projects_router)
app.include_router(reconciliation_router)
app.include_router(reports_router)
app.include_router(webhooks_router)
