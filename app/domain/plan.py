"""Dry-run plan domain models."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class OperationType(StrEnum):
    """Write operation categories that can be previewed before apply."""

    CREATE_PROJECT_FOLDER = "CREATE_PROJECT_FOLDER"
    CREATE_REPORT_FOLDER = "CREATE_REPORT_FOLDER"
    UPDATE_SMARTSHEET_ROW = "UPDATE_SMARTSHEET_ROW"
    ADD_SMARTSHEET_ATTACHMENT_LINK = "ADD_SMARTSHEET_ATTACHMENT_LINK"
    CREATE_DATABASE_RECORD = "CREATE_DATABASE_RECORD"


class OperationRiskLevel(StrEnum):
    """Risk level assigned to a planned operation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PlanOperation(BaseModel):
    """One proposed write operation in a dry-run plan."""

    model_config = ConfigDict(frozen=True)

    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    operation_type: OperationType
    target: str
    reason: str
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    risk_level: OperationRiskLevel
    dry_run_result: str


class Plan(BaseModel):
    """A dry-run preview of proposed write operations."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    blueprint_path: str
    operation_count: int
    operations: list[PlanOperation]
    warnings: list[str] = Field(default_factory=list)
