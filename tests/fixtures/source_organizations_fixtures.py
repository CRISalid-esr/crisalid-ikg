import pytest_asyncio

from app.models.source_organizations import SourceOrganization


@pytest_asyncio.fixture(name="hal_source_institution_pydantic_model")
async def fixture_hal_source_institution_pydantic_model(
        hal_source_institution_json_data) -> SourceOrganization:
    """
    Create a source journal pydantic model
    :param hal_source_institution_json_data:
    :return: basic source record pydantic model from ScanR data
    """
    return SourceOrganization(**hal_source_institution_json_data)


@pytest_asyncio.fixture(name="hal_source_laboratory_pydantic_model")
async def fixture_hal_source_laboratory_pydantic_model(
        hal_source_laboratory_json_data) -> SourceOrganization:
    """
    Create a source journal pydantic model
    :param hal_source_laboratory_json_data:
    :return: basic source record pydantic model from ScanR data
    """
    return SourceOrganization(**hal_source_laboratory_json_data)


@pytest_asyncio.fixture(name="hal_source_org_without_type_pydantic_model")
async def fixture_hal_source_org_without_type_pydantic_model(
        hal_source_org_without_type_json_data) -> SourceOrganization:
    """
    Create a source organization pydantic model without type
    :param hal_source_org_without_type_json_data:
    :return:
    """
    return SourceOrganization(**hal_source_org_without_type_json_data)


@pytest_asyncio.fixture(name="hal_source_institution_json_data")
async def fixture_hal_source_institution_json_data() -> dict[str, str]:
    """
    Create a source journal pydantic model
    :return: basic source record pydantic model from ScanR data
    """
    return {
        "source": "hal",
        "source_identifier": "2001",
        "name": "Université Anonyme",
        "type": "institution",
        "identifiers": [
            {
                "type": "hal",
                "value": "2001"
            },
            {
                "type": "idref",
                "value": "123456789"
            },
            {
                "type": "isni",
                "value": "000000012345678X"
            },
            {
                "type": "ror",
                "value": "https://ror.org/000000000"
            }
        ]
    }


@pytest_asyncio.fixture(name="hal_source_laboratory_json_data")
async def fixture_hal_source_laboratory_json_data() -> dict[str, str]:
    """
    Create a source journal pydantic model
    :return: basic source record pydantic model from ScanR data
    """
    return {
        "source": "hal",
        "source_identifier": "3002",
        "name": "Laboratoire Interdisciplinaire",
        "type": "laboratory",
        "identifiers": [
            {
                "type": "hal",
                "value": "3002"
            },
            {
                "type": "ror",
                "value": "https://ror.org/000000001"
            }
        ]
    }


@pytest_asyncio.fixture(name="hal_source_org_without_type_json_data")
async def fixture_hal_source_org_without_type_json_data() -> dict[str, str]:
    """
    Create source organization json data without type
    :return:
    """
    return {
        "source": "hal",
        "source_identifier": "9999",
        "name": "Organization Without Type",
        "identifiers": [
            {"type": "hal", "value": "9999"}
        ]
    }
