import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.http.aio_http_client_manager import AioHttpClientManager
from app.services.documents.unpaywall_service import UnpaywallService

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/unpaywall")


@pytest.fixture(name="mock_unpaywall_portal")
def mock_unpaywall_portal():
    """
    Patch AioHttpClientManager.get_session to mock session.get(url) as an async context manager.
    """
    requested_urls = []

    def _mock_get(url, *args, **kwargs):  # pylint: disable=unused-argument
        requested_urls.append(url)
        if "10.1017/ash.2023.207" in url:
            body = _load_unpaywall_json_ld_file("doi1.json")
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


@pytest.fixture(name="mock_unpaywall_service", autouse=True)
def fixture_mock_unpaywall_service():
    """
    Mock the Unpaywall service response for testing.
    :return:
    """

    async def mock_get_data(doi: str):
        if doi in ["10.1017/ash.2023.207"]:
            return UnpaywallService.UpwResponseSchema(
                upw_success = True,
                upw_status = 'gold',
                repository_location = True,
                doaj_success = True,
                embargo_date = None,
            )
        return UnpaywallService.UpwResponseSchema(
                upw_success = False,
                upw_status = None,
                repository_location = None,
                doaj_success = None,
                embargo_date = None,
            )
    async_mock = AsyncMock(side_effect=mock_get_data)

    with patch.object(UnpaywallService, "get_data", async_mock):
        yield


def _load_unpaywall_json_ld_file(filename: str) -> str:
    with open(os.path.join(TEST_DATA_PATH, filename), encoding="utf-8") as f:
        return f.read()
