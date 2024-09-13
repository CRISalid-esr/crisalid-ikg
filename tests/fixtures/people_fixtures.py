import pytest_asyncio

from app.models.people import Person
from tests.fixtures.common import _person_json_data_from_file, _person_from_json_data


@pytest_asyncio.fixture(name="basic_person_pydantic_model")
async def fixture_basic_person_pydantic_model(_base_path) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(_person_json_data_from_file(_base_path, "basic_person"))


@pytest_asyncio.fixture(name="basic_person_json_data")
async def fixture_basic_person_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "basic_person")


@pytest_asyncio.fixture(name="person_with_invalid_identifier_type_json_data")
async def fixture_person_with_invalid_identifier_type_json_data(_base_path) -> dict:
    """
    Create a person with invalid identifier type json data
    :return: person with invalid identifier type json data
    """
    return _person_json_data_from_file(_base_path, "person_with_invalid_identifier_type")
