import pytest

from app.services.documents.unpaywall_service import UnpaywallService

@pytest.mark.asyncio
async def test_check_upw_with_real_parsing():
    """
    Test the UnpaywallService with a real parsing of the (mocked) Unpaywall portal data.
    :param mock_unpaywall_portal: Mocked Unpaywall portal data.
    :return: None
    """

    service = UnpaywallService()
    info = await service.get_data("10.1017/ash.2023.207")

    # Assert returned object
    assert info.upw_success
    assert info.doaj_success
    assert info.embargo_date is None
    assert info.repository_location
    assert info.upw_status == 'gold'
