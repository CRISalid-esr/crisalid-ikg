import pytest_asyncio

from app.models.research_structures import ResearchStructure
from tests.fixtures.common import _research_structure_from_json_data, \
    _organization_json_data_from_file


@pytest_asyncio.fixture(name="basic_research_structure_pydantic_model")
async def fixture_basic_research_structure_pydantic_model(_base_path) -> ResearchStructure:
    """
    Create a basic structure pydantic model
    :return: basic structure pydantic model
    """
    return _research_structure_from_json_data(_organization_json_data_from_file(
        _base_path,
        "basic_research_structure")
    )


@pytest_asyncio.fixture(name="basic_research_structure_json_data")
async def fixture_basic_research_structure_json_data(_base_path) -> dict:
    """
    Create a basic structure json data
    :return: basic structure json data
    """
    return _organization_json_data_from_file(_base_path, "basic_research_structure")


@pytest_asyncio.fixture(name="research_structure_with_invalid_identifier_type_json_data")
async def fixture_research_structure_with_invalid_identifier_type_json_data(_base_path) -> dict:
    """
    Create a structure with invalid identifier type json data
    :return: structure with invalid identifier type json data
    """
    return _organization_json_data_from_file(_base_path,
                                             "research_structure_with_invalid_identifier_type")
