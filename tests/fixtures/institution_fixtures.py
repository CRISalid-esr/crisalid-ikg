from unittest.mock import AsyncMock, patch

import pytest

from app.services.organizations.institution_registry_service import InstitutionRegistryService
from tests.fixtures.common import _json_data_from_file


@pytest.fixture(autouse=True)
def mock_query_institution_from_external_source(_base_path):
    """
    Mock the query to the external source for institutions
    :param _base_path:
    :return:
    """
    institutions_data = {
        "0751818J": _json_data_from_file(_base_path, "data/institutions/university_1.json"),
        "0833945M": _json_data_from_file(_base_path, "data/institutions/university_2.json"),
        "0310890B": _json_data_from_file(_base_path, "data/institutions/university_3.json"),
    }

    async def mock_fetch(identifiers):
        for identifier in identifiers:
            if identifier.value in institutions_data:
                return institutions_data[identifier.value]
        return None

    with patch.object(InstitutionRegistryService, '_query_external_source',
                      AsyncMock(side_effect=mock_fetch)):
        yield
