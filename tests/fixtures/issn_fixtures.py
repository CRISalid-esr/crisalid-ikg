import os
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from app.http.aio_http_client_manager import AioHttpClientManager
from app.models.journal_identifiers import JournalIdentifier
from app.services.journals.issn_info import IssnInfo
from app.services.journals.issn_service import ISSNService

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/issn")


@pytest.fixture(autouse=True)
def mock_issn_portal():
    """
    Patch AioHttpClientManager.get_session to mock session.get(url) as an async context manager.
    """
    requested_urls = []

    def _mock_get(url, *args, **kwargs):  # pylint: disable=unused-argument
        requested_urls.append(url)
        if "0967-070X" in url:
            body = _load_issn_json_ld_file("0967-070X.json")
            status = 200
        elif "1879-310X" in url:
            body = _load_issn_json_ld_file("1879-310X.json")
            status = 200
        else:
            body = "Not Found"
            status = 404

        # Build mock response
        mock_resp = AsyncMock()
        mock_resp.status = status
        mock_resp.text = AsyncMock(return_value=body)

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


@pytest.fixture(name="mock_issn_service", autouse=True)
def fixture_mock_issn_service():
    """
    Mock the ISSN service response for testing.
    :return:
    """

    async def mock_check_identifier(identifier: JournalIdentifier):
        if identifier.value in ["1943-5606", "1090-0241"]:
            return IssnInfo(
                checked_issn=identifier.value,
                issn_l='1090-0241',
                related_issns_with_format={
                    '1090-0241': "Print",
                    '1943-5606': "Online",
                },
                title="Journal of Geotechnical and Geoenvironmental Engineering",
                urls=["http://journalA.example.org"]
            )
        return IssnInfo(
            checked_issn="0007-4217",
            issn_l="0007-4217",
            related_issns_with_format={
                "0007-4217": "Print",
                "2241-0104": "Online",
                "1234-5678": "Unknown"
            },
            title="Sample Journal Title",
            urls=["http://journal.example.org"]
        )
    async_mock = AsyncMock(side_effect=mock_check_identifier)

    with patch.object(ISSNService, "check_identifier", async_mock):
        yield


def _load_issn_json_ld_file(filename: str) -> str:
    with open(os.path.join(TEST_DATA_PATH, filename), encoding="utf-8") as f:
        return f.read()
