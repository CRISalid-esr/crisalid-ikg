import pytest

from app.services.documents.unpaywall_service import UnpaywallService


@pytest.fixture(name="mock_unpaywall_service", autouse=True)
def fixture_mock_unpaywall_service():
    """Disable mock"""
    return

@pytest.mark.asyncio
async def test_check_upw_with_real_parsing(mock_unpaywall_portal):
    """
    Test the UnpaywallService with a real parsing of the (mocked) Unpaywall portal data.
    :param mock_unpaywall_portal: Mocked Unpaywall portal data.
    :return: None
    """

    requested_urls = mock_unpaywall_portal

    service = UnpaywallService()
    info = await service.get_data("10.1017/ash.2023.207")

    # Assert URLs were fetched
    assert len(requested_urls) == 1
    assert (requested_urls[0] ==
            "https://api.unpaywall.org//10.1017/ash.2023.207?email=test@test.com")

    # Assert returned object
    assert info.upw_success
    assert info.doaj_success
    assert info.embargo_date is None
    assert info.repository_location
    assert info.upw_status == 'gold'
