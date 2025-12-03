import pytest

from app.services.documents.doaj_service import DoajService


@pytest.fixture(name="mock_doaj_service", autouse=True)
def fixture_mock_doaj_service():
    """Disable mock"""
    return


@pytest.mark.asyncio
async def test_check_doaj_with_real_parsing(mock_doaj_portal):
    """
    Test the DoajService with a real parsing of the (mocked) Doaj portal data.
    :param mock_doaj_portal: Mocked DOAJ portal data.
    :return: None
    """
    requested_urls = mock_doaj_portal

    service = DoajService()
    info = await service.get_apc_status("0967-070X")

    # Assert URLs were fetched
    assert len(requested_urls) == 1
    assert requested_urls[0] == "https://doaj.org/api/search/journals/issn:0967-070X"

    # Assert returned object
    assert not info.doaj_success
    assert info.has_apc is None

    service = DoajService()
    info = await service.get_apc_status("2732-494X")

    # Assert returned object
    assert info.doaj_success
    assert info.has_apc
