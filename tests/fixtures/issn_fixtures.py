from unittest.mock import AsyncMock, patch

import pytest

from app.services.journals.issn_info import IssnInfo
from app.services.journals.issn_service import ISSNService


@pytest.fixture(autouse=True)
def mock_issn_portal():
    """
    Mock the ISSN service response for testing.
    :return:
    """
    mock_info = IssnInfo(
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

    async_mock = AsyncMock(return_value=mock_info)

    with patch.object(ISSNService, "check_identifier", async_mock):
        yield
