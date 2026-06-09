"""Smartsheet API client with guarded write support."""

from collections.abc import Iterable
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field
import structlog
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import SmartsheetSettings, get_settings
from app.utils.redaction import redact

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class SmartsheetError(Exception):
    """Raised when Smartsheet returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = redact(response_body)


class SmartsheetSafetyError(ValueError):
    """Raised when a write operation lacks required safety approval."""


class SmartsheetWriteSafetyContext(BaseModel):
    """Proof that a Smartsheet write was approved through a dry-run plan."""

    model_config = ConfigDict(frozen=True)

    dry_run_completed: bool
    enable_write_operations: bool
    apply_requested: bool
    operation_id: str
    approved_operation_ids: frozenset[str] = Field(default_factory=frozenset)
    plan_path: str

    def require_approved(self) -> None:
        """Raise unless all write safety controls are satisfied."""
        missing_controls: list[str] = []
        if not self.dry_run_completed:
            missing_controls.append("dry_run_completed")
        if not self.enable_write_operations:
            missing_controls.append("ENABLE_WRITE_OPERATIONS")
        if not self.apply_requested:
            missing_controls.append("--apply")
        if self.operation_id not in self.approved_operation_ids:
            missing_controls.append("approved_plan_operation")

        if missing_controls:
            formatted = ", ".join(missing_controls)
            raise SmartsheetSafetyError(f"Smartsheet write safety controls missing: {formatted}")


class SmartsheetClient:
    """Smartsheet API client with read methods and safety-gated writes."""

    def __init__(
        self,
        *,
        settings: SmartsheetSettings | None = None,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
        retry_attempts: int = 3,
        logger: Any | None = None,
    ) -> None:
        self._settings = settings or get_settings().smartsheet
        self._client = client or httpx.Client(
            base_url=self._settings.base_url.rstrip("/"),
            headers=self._headers(),
            timeout=timeout,
        )
        self._owns_client = client is None
        self._retry_attempts = retry_attempts
        self._logger = logger or structlog.get_logger("smartsheet")

    def close(self) -> None:
        """Close the underlying HTTP client if this instance created it."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "SmartsheetClient":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def whoami(self) -> dict[str, Any]:
        """Return the current Smartsheet user."""
        return self._get("/users/me")

    def list_workspaces(self) -> list[dict[str, Any]]:
        """Return all visible Smartsheet workspaces."""
        return self._get_paginated("/workspaces")

    def list_sheets(self) -> list[dict[str, Any]]:
        """Return all visible Smartsheet sheets."""
        return self._get_paginated("/sheets")

    def get_sheet(
        self,
        sheet_id: str,
        *,
        include: str | Iterable[str] | None = None,
        page_size: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Return one sheet by ID with optional Smartsheet query parameters."""
        params: dict[str, str | int] = {}
        if include:
            params["include"] = _format_include(include)
        if page_size is not None:
            params["pageSize"] = page_size
        if page is not None:
            params["page"] = page

        return self._get(f"/sheets/{sheet_id}", params=params)

    def list_row_attachments(self, sheet_id: str, row_id: str) -> list[dict[str, Any]]:
        """Return attachment metadata for one row without downloading file contents."""
        return self._get_paginated(f"/sheets/{sheet_id}/rows/{row_id}/attachments")

    def get_attachment_metadata(self, sheet_id: str, attachment_id: str) -> dict[str, Any]:
        """Return one attachment metadata record without downloading file contents."""
        return self._get(f"/sheets/{sheet_id}/attachments/{attachment_id}")

    def download_attachment_content(self, source_url: str) -> bytes:
        """Download attachment bytes from an explicit source URL."""
        try:
            response = self._client.get(source_url)
        except httpx.HTTPError as exc:
            raise SmartsheetError("Smartsheet attachment download failed") from exc

        if response.status_code >= 400:
            raise SmartsheetError(
                f"Smartsheet returned HTTP {response.status_code}",
                status_code=response.status_code,
                response_body=_response_json(response),
            )

        return response.content

    def update_row_cells(
        self,
        sheet_id: str,
        row_id: str,
        cells: list[dict[str, Any]],
        *,
        safety_context: SmartsheetWriteSafetyContext,
    ) -> dict[str, Any]:
        """Update Smartsheet row cells only with an approved write safety context."""
        safety_context.require_approved()
        if not cells:
            raise SmartsheetSafetyError("At least one cell is required for Smartsheet write-back")

        payload = [{"id": row_id, "cells": cells}]
        return self._put(f"/sheets/{sheet_id}/rows", json_body=payload)

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._settings.access_token:
            headers["Authorization"] = f"Bearer {self._settings.access_token}"
        return headers

    def _get_paginated(self, path: str, *, page_size: int = 100) -> list[dict[str, Any]]:
        page = 1
        items: list[dict[str, Any]] = []

        while True:
            response = self._get(path, params={"pageSize": page_size, "page": page})
            data = response.get("data", [])
            if not isinstance(data, list):
                raise SmartsheetError("Smartsheet pagination response did not include a data list")

            items.extend(item for item in data if isinstance(item, dict))

            total_pages = int(response.get("totalPages") or page)
            if page >= total_pages:
                return items

            page += 1

    def _get(self, path: str, *, params: dict[str, str | int] | None = None) -> dict[str, Any]:
        self._logger.info("smartsheet_get", path=path, params=params or {})

        for attempt in Retrying(
            retry=retry_if_exception(_is_retryable_error),
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.01, max=0.1),
            reraise=True,
        ):
            with attempt:
                return self._get_once(path, params=params)

        raise SmartsheetError("Smartsheet request retry loop exited unexpectedly")

    def _put(self, path: str, *, json_body: Any) -> dict[str, Any]:
        self._logger.info("smartsheet_put", path=path)

        for attempt in Retrying(
            retry=retry_if_exception(_is_retryable_error),
            stop=stop_after_attempt(self._retry_attempts),
            wait=wait_exponential(multiplier=0.01, max=0.1),
            reraise=True,
        ):
            with attempt:
                return self._put_once(path, json_body=json_body)

        raise SmartsheetError("Smartsheet request retry loop exited unexpectedly")

    def _get_once(
        self,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise SmartsheetError("Smartsheet request failed") from exc

        response_body = _response_json(response)
        if response.status_code >= 400:
            raise SmartsheetError(
                f"Smartsheet returned HTTP {response.status_code}",
                status_code=response.status_code,
                response_body=response_body,
            )

        if isinstance(response_body, dict):
            return response_body

        raise SmartsheetError("Smartsheet response was not a JSON object")

    def _put_once(self, path: str, *, json_body: Any) -> dict[str, Any]:
        try:
            response = self._client.put(path, json=json_body)
        except httpx.HTTPError as exc:
            raise SmartsheetError("Smartsheet request failed") from exc

        response_body = _response_json(response)
        if response.status_code >= 400:
            raise SmartsheetError(
                f"Smartsheet returned HTTP {response.status_code}",
                status_code=response.status_code,
                response_body=response_body,
            )

        if isinstance(response_body, dict):
            return response_body

        raise SmartsheetError("Smartsheet response was not a JSON object")


def _is_retryable_error(exc: BaseException) -> bool:
    return isinstance(exc, SmartsheetError) and exc.status_code in RETRYABLE_STATUS_CODES


def _response_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"text": response.text}


def _format_include(include: str | Iterable[str]) -> str:
    if isinstance(include, str):
        return include

    return ",".join(include)
