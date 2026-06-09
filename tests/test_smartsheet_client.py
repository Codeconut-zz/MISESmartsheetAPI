from typing import Any

import httpx
import pytest
import respx

from app.config import SmartsheetSettings
from app.connectors.smartsheet_client import SmartsheetClient, SmartsheetError

BASE_URL = "https://api.smartsheet.test/2.0"
TOKEN = "test-token-value"


class FakeLogger:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.events.append({"event": event, **kwargs})


def make_client(logger: FakeLogger | None = None) -> SmartsheetClient:
    return SmartsheetClient(
        settings=SmartsheetSettings(
            base_url=BASE_URL,
            access_token=TOKEN,
            tir_sheet_id="sheet-123",
        ),
        retry_attempts=2,
        logger=logger,
    )


@respx.mock
def test_whoami_sends_read_only_get_with_auth_header() -> None:
    route = respx.get(f"{BASE_URL}/users/me").mock(
        return_value=httpx.Response(200, json={"email": "me@test"})
    )

    with make_client() as client:
        response = client.whoami()

    assert response == {"email": "me@test"}
    assert route.calls[0].request.method == "GET"
    assert route.calls[0].request.headers["Authorization"] == f"Bearer {TOKEN}"


@respx.mock
def test_list_workspaces_paginates() -> None:
    respx.get(f"{BASE_URL}/workspaces", params={"pageSize": 100, "page": 1}).mock(
        return_value=httpx.Response(
            200,
            json={"pageNumber": 1, "totalPages": 2, "data": [{"id": "workspace-1"}]},
        )
    )
    respx.get(f"{BASE_URL}/workspaces", params={"pageSize": 100, "page": 2}).mock(
        return_value=httpx.Response(
            200,
            json={"pageNumber": 2, "totalPages": 2, "data": [{"id": "workspace-2"}]},
        )
    )

    with make_client() as client:
        response = client.list_workspaces()

    assert response == [{"id": "workspace-1"}, {"id": "workspace-2"}]


@respx.mock
def test_list_sheets_and_get_sheet() -> None:
    respx.get(f"{BASE_URL}/sheets", params={"pageSize": 100, "page": 1}).mock(
        return_value=httpx.Response(200, json={"totalPages": 1, "data": [{"id": "sheet-1"}]})
    )
    sheet_route = respx.get(
        f"{BASE_URL}/sheets/sheet-1",
        params={"include": "attachments,discussions", "pageSize": 50, "page": 2},
    ).mock(return_value=httpx.Response(200, json={"id": "sheet-1"}))

    with make_client() as client:
        sheets = client.list_sheets()
        sheet = client.get_sheet(
            "sheet-1",
            include=["attachments", "discussions"],
            page_size=50,
            page=2,
        )

    assert sheets == [{"id": "sheet-1"}]
    assert sheet == {"id": "sheet-1"}
    assert sheet_route.called


@pytest.mark.parametrize("status_code", [401, 403])
@respx.mock
def test_client_raises_for_auth_errors(status_code: int) -> None:
    respx.get(f"{BASE_URL}/users/me").mock(
        return_value=httpx.Response(status_code, json={"message": "not allowed"})
    )

    with make_client() as client, pytest.raises(SmartsheetError) as exc_info:
        client.whoami()

    assert exc_info.value.status_code == status_code


@pytest.mark.parametrize("status_code", [429, 500])
@respx.mock
def test_client_retries_transient_errors(status_code: int) -> None:
    route = respx.get(f"{BASE_URL}/users/me").mock(
        side_effect=[
            httpx.Response(status_code, json={"message": "try again"}),
            httpx.Response(200, json={"email": "me@test"}),
        ]
    )

    with make_client() as client:
        response = client.whoami()

    assert response == {"email": "me@test"}
    assert route.call_count == 2


@respx.mock
def test_token_is_not_logged() -> None:
    logger = FakeLogger()
    respx.get(f"{BASE_URL}/users/me").mock(
        return_value=httpx.Response(200, json={"email": "me@test"})
    )

    with make_client(logger=logger) as client:
        client.whoami()

    assert TOKEN not in str(logger.events)
