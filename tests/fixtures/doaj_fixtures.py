import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.http.aio_http_client_manager import AioHttpClientManager
from app.services.documents.doaj_service import DoajService

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/doaj")


@pytest.fixture(name="mock_doaj_portal")
def mock_doaj_portal():
    """
    Patch AioHttpClientManager.get_session to mock session.get(url) as an async context manager.
    """
    requested_urls = []

    def _mock_get(url, *args, **kwargs):  # pylint: disable=unused-argument
        requested_urls.append(url)
        if "2732-494X" in url:
            body = _load_doaj_json_ld_file("2732-494X.json")
            status = 200
        else:
            body = "Not Found"
            status = 404

        # Build mock response
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.json = AsyncMock(return_value=body)

        # Wrap in async context manager
        mock_ctx_manager = AsyncMock()
        mock_ctx_manager.__aenter__.return_value = mock_resp
        mock_ctx_manager.__aexit__.return_value = None
        return mock_ctx_manager

    # Mock session with .get()
    mock_session = MagicMock()
    mock_session.get.side_effect = _mock_get

    # Patch the AioHttpClientManager to return our mock session
    with patch.object(AioHttpClientManager, "get_session",
                      new=AsyncMock(return_value=mock_session)):
        yield requested_urls

@pytest.fixture(name="mock_doaj_service", autouse=True)
def fixture_mock_doaj_service():
    """
    Mock the DOAJ service response for testing.
    :return:
    """

    async def mock_get_apc_status(issn: str):
        if issn in ["2732-494X"]:
            return DoajService.DoajResponseSchema(
                doaj_success = True,
                has_apc = True
            )
        return DoajService.DoajResponseSchema(
            doaj_success=False,
            has_apc=None
        )
    async_mock = AsyncMock(side_effect=mock_get_apc_status)

    with patch.object(DoajService, "get_apc_status", async_mock):
        yield


def _load_doaj_json_ld_file(filename: str) -> str:
    with open(os.path.join(TEST_DATA_PATH, filename), encoding="utf-8") as f:
        return f.read()
