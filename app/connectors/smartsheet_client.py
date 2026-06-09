"""Read-only Smartsheet API client."""

from collections.abc import Iterable
from typing import Any

import httpx
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


class SmartsheetClient:
    """Read-only Smartsheet API client."""

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
