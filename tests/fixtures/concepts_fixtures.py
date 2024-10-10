import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.concept_dao import ConceptDAO
from app.models.concepts import Concept
from tests.fixtures.common import _concept_from_json_data, _concept_json_data_from_file


@pytest_asyncio.fixture(name="persisted_concept_a_pydantic_model")
async def fixture_persisted_concept_a_pydantic_model(concept_a_pydantic_model) -> Concept:
    """
    Create a basic persisted concept pydantic model
    :return: basic persisted concept pydantic model
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    concept_dao: ConceptDAO = factory.get_dao(Concept)
    await concept_dao.create(concept_a_pydantic_model)
    return concept_a_pydantic_model


@pytest_asyncio.fixture(name="concept_a_pydantic_model")
async def fixture_concept_a_pydantic_model(concept_a_json_data) -> Concept:
    """
    Create a basic concept pydantic model
    :return: basic concept pydantic model
    """
    return _concept_from_json_data(concept_a_json_data)


@pytest_asyncio.fixture(name="concept_a_json_data")
async def fixture_concept_a_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _concept_json_data_from_file(_base_path, "concept_a")


@pytest_asyncio.fixture(name="persisted_concept_b_without_uri_pydantic_model")
async def fixture_persisted_concept_b_without_uri_pydantic_model(
        concept_b_without_uri_pydantic_model) -> Concept:
    """
    Create a basic persisted concept pydantic model
    :return: basic persisted concept pydantic model
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    concept_dao: ConceptDAO = factory.get_dao(Concept)
    await concept_dao.create(concept_b_without_uri_pydantic_model)
    return concept_b_without_uri_pydantic_model


@pytest_asyncio.fixture(name="concept_b_without_uri_pydantic_model")
async def fixture_concept_b_without_uri_pydantic_model(concept_b_without_uri_json_data) -> Concept:
    """
    Create a basic concept pydantic model
    :return: basic concept pydantic model
    """
    return _concept_from_json_data(concept_b_without_uri_json_data)


@pytest_asyncio.fixture(name="concept_b_without_uri_json_data")
async def fixture_concept_b_without_uri_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _concept_json_data_from_file(_base_path, "concept_b_without_uri")


@pytest_asyncio.fixture(name="invalid_concept_b_without_uri_json_data")
async def fixture_invalid_concept_b_without_uri_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _concept_json_data_from_file(_base_path, "invalid_concept_b_without_uri")
