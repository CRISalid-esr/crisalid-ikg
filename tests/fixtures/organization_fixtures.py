import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.research_structures import ResearchStructure
from tests.fixtures.common import _research_structure_from_json_data, \
    _organization_json_data_from_file


@pytest_asyncio.fixture(name="persisted_research_structure_pydantic_model")
async def fixture_persisted_research_structure_pydantic_model(
        research_structure_pydantic_model) -> ResearchStructure:
    """
    Create a basic persisted research structure pydantic model
    :return: basic persisted research structure pydantic model
    """
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_pydantic_model)
    return research_structure_pydantic_model


@pytest_asyncio.fixture(name="research_structure_pydantic_model")
async def fixture_research_structure_pydantic_model(
        research_structure_json_data) -> ResearchStructure:
    """
    Create a basic structure pydantic model
    :return: basic structure pydantic model
    """
    return _research_structure_from_json_data(research_structure_json_data)


@pytest_asyncio.fixture(name="research_structure_json_data")
async def fixture_research_structure_json_data(_base_path) -> dict:
    """
    Create a basic structure json data
    :return: basic structure json data
    """
    return _organization_json_data_from_file(_base_path, "research_structure")


@pytest_asyncio.fixture(name="research_structure_with_updated_name_pydantic_model")
async def fixture_research_structure_with_updated_name_pydantic_model(
        research_structure_with_updated_name_json_data) -> ResearchStructure:
    """
    Create a basic structure pydantic model
    :return: basic structure pydantic model
    """
    return _research_structure_from_json_data(research_structure_with_updated_name_json_data)


@pytest_asyncio.fixture(name="research_structure_with_updated_name_json_data")
async def fixture_research_structure_with_updated_name_json_data(_base_path) -> dict:
    """
    Create a basic structure json data
    :return: basic structure json data
    """
    return _organization_json_data_from_file(_base_path, "research_structure_with_updated_name")


@pytest_asyncio.fixture(name="persisted_research_structure_with_different_ids_pydantic_model")
async def fixture_persisted_research_structure_with_different_ids_pydantic_model(
        research_structure_with_different_ids_pydantic_model) -> ResearchStructure:
    """
    Create a basic persisted research structure pydantic model
    :return: basic persisted research structure pydantic model
    """
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_with_different_ids_pydantic_model)
    return research_structure_with_different_ids_pydantic_model


@pytest_asyncio.fixture(name="research_structure_with_different_ids_pydantic_model")
async def fixture_research_structure_with_different_ids_pydantic_model(
        research_structure_with_different_ids_json_data) -> ResearchStructure:
    """
    Create a basic structure pydantic model
    :return: basic structure pydantic model
    """
    return _research_structure_from_json_data(research_structure_with_different_ids_json_data)


@pytest_asyncio.fixture(name="research_structure_with_different_ids_json_data")
async def fixture_research_structure_with_different_ids_json_data(_base_path) -> dict:
    """
    Create a basic structure json data
    :return: basic structure json data
    """
    return _organization_json_data_from_file(
        _base_path, "research_structure_with_different_identifiers"
    )


@pytest_asyncio.fixture(name="research_structure_with_invalid_identifier_type_json_data")
async def fixture_research_structure_with_invalid_identifier_type_json_data(_base_path) -> dict:
    """
    Create a structure with invalid identifier type json data
    :return: structure with invalid identifier type json data
    """
    return _organization_json_data_from_file(_base_path,
                                             "research_structure_with_invalid_identifier_type")


@pytest_asyncio.fixture(name="research_structure_with_duplicate_identifiers_json_data")
async def fixture_research_structure_with_duplicate_identifiers_json_data(_base_path) -> dict:
    """
    Create a basic structure json data
    :return: basic structure json data
    """
    return _organization_json_data_from_file(
        _base_path, "research_structure_with_duplicate_identifiers")
