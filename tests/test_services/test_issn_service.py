import os

import pytest

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier
from app.services.journals.issn_service import ISSNService


@pytest.fixture(name="mock_issn_service", autouse=True)
def fixture_mock_issn_service():
    """Disable mock for AbesConceptSolver."""
    return


@pytest.mark.asyncio
async def test_check_identifier_with_real_parsing(mock_issn_portal):
    """
    Test the ISSNService with a real parsing of the (mocked) ISSN portal data.
    :param mock_issn_portal: Mocked ISSN portal data.
    :return: None
    """
    requested_urls = mock_issn_portal

    identifier = JournalIdentifier(
        uid="issn-0967-070X",
        type=JournalIdentifierType.ISSN,
        format=None,
        value="0967-070X",
        last_checked=None,
    )

    service = ISSNService()
    info = await service.check_identifier(identifier)

    # Assert URLs were fetched
    assert len(requested_urls) == 2
    assert requested_urls[0] == "https://portal.issn.org/resource/ISSN/0967-070X?format=json"
    assert requested_urls[1] == "https://portal.issn.org/resource/ISSN/1879-310X?format=json"

    # Assert returned object
    assert info.checked_issn == "0967-070X"
    assert info.issn_l == "0967-070X"
    assert info.title == "Transport policy."
    assert set(info.related_issns_with_format.keys()) == {"0967-070X", "1879-310X"}
    assert info.related_issns_with_format["0967-070X"] == "Print"
    assert info.related_issns_with_format["1879-310X"] == "Online"
    assert info.urls == ["http://www.sciencedirect.com/science/journal/0967070X"]
    assert info.errors == []


def _load_ttl_file(filename: str) -> str:
    base = os.path.join(os.path.dirname(__file__), "../../data/issn")
    with open(os.path.join(base, filename), encoding="utf-8") as f:
        return f.read()
