"""Report summary read API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.api.schemas import ReportSummaryResponse
from app.storage.repositories import ReportingRepository

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummaryResponse)
def get_report_summary(
    session: Session = Depends(get_db_session),
) -> ReportSummaryResponse:
    """Return report summary counts."""
    return ReportSummaryResponse(summary=ReportingRepository().summary(session))
