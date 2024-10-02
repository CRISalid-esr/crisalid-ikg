import pytest_asyncio

from app.models.concepts import Concept
from tests.fixtures.common import _concept_from_json_data, _concept_json_data_from_file


@pytest_asyncio.fixture(name="concept_pydantic_model")
async def fixture_concept_pydantic_model(concept_json_data) -> Concept:
    """
    Create a basic concept pydantic model
    :return: basic concept pydantic model
    """
    return _concept_from_json_data(concept_json_data)


@pytest_asyncio.fixture(name="concept_json_data")
async def fixture_concept_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _concept_json_data_from_file(_base_path, "concept")


@pytest_asyncio.fixture(name="concept_without_uri_json_data")
async def fixture_concept_without_uri_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _concept_json_data_from_file(_base_path, "concept_without_uri")
