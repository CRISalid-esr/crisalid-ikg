import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.models.people import Person
from tests.fixtures.common import _person_from_json_data, _person_json_data_from_file


@pytest_asyncio.fixture(name="persisted_person_a_pydantic_model")
async def fixture_persisted_person_a_pydantic_model(person_a_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic persisted person pydantic model
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    people_dao: PersonDAO = factory.get_dao(Person)
    await people_dao.create(person_a_pydantic_model)
    return person_a_pydantic_model


@pytest_asyncio.fixture(name="person_a_pydantic_model")
async def fixture_person_a_pydantic_model(person_a_json_data) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_a_json_data)


@pytest_asyncio.fixture(name="person_a_json_data")
async def fixture_person_a_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_a")


@pytest_asyncio.fixture(name="person_a_with_different_membership_pydantic_model")
async def fixture_person_a_with_different_membership_pydantic_model(
        person_a_with_different_membership_json_data,
) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_a_with_different_membership_json_data)


@pytest_asyncio.fixture(name="person_a_with_different_membership_json_data")
async def fixture_person_a_with_different_membership_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_different_membership")


@pytest_asyncio.fixture(name="person_a_with_implicit_local_membership_identifier_json_data")
async def fixture_person_a_with_implicit_local_membership_identifier_json_data(_base_path) -> dict:
    """
    Create a person json data with membership entity uid without the "local" prefix
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path,
                                       "person_a_with_implicit_local_membership_identifier"
                                       )


@pytest_asyncio.fixture(name="person_b_with_two_names_pydantic_model")
async def fixture_person_b_with_two_names_pydantic_model(_base_path) -> Person:
    """
    Create a basic person pydantic model with two names
    :return: basic person pydantic model with two names
    """
    return _person_from_json_data(
        _person_json_data_from_file(_base_path, "person_b_with_two_names")
    )


@pytest_asyncio.fixture(name="person_a_with_name_in_multiple_lng_pydantic_model")
async def fixture_person_a_with_name_in_multiple_lng_pydantic_model(
        person_a_with_name_in_multiple_lng_json_data) -> Person:
    """
    Create a person with name in multiple languages pydantic model
    :return: person with name in multiple languages pydantic model
    """
    return _person_from_json_data(person_a_with_name_in_multiple_lng_json_data)


@pytest_asyncio.fixture(name="person_a_with_name_in_multiple_lng_json_data")
async def fixture_person_a_with_name_in_multiple_lng_json_data(_base_path) -> dict:
    """
    Create a person with name in multiple languages json data
    :return: person with name in multiple languages json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_name_in_multiple_lng")


@pytest_asyncio.fixture(name="person_a_with_invalid_identifier_type_json_data")
async def fixture_person_a_with_invalid_identifier_type_json_data(_base_path) -> dict:
    """
    Create a person with invalid identifier type json data
    :return: person with invalid identifier type json data
    """
    return _person_json_data_from_file(
        _base_path, "person_a_with_invalid_identifier_type"
    )


@pytest_asyncio.fixture(name="person_a_with_two_orcid_json_data")
async def fixture_person_a_with_two_orcid_json_data(_base_path) -> dict:
    """
    Create a person with multiple orcid json data
    :return: person with multiple orcid json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_two_orcid")


@pytest_asyncio.fixture(name="person_c_with_two_last_names_json_data")
async def fixture_person_c_with_two_last_names_json_data(_base_path) -> dict:
    """
    Create a person with two last names json data
    :return: person with two last names json data
    """
    return _person_json_data_from_file(_base_path, "person_c_with_two_last_names")


@pytest_asyncio.fixture(name="person_with_mononym_pydantic_model")
async def fixture_person_with_mononym_pydantic_model(person_with_mononym_json_data) -> Person:
    """
    Create a basic person pydantic model with mononym
    :return: basic person pydantic model with mononym
    """
    return _person_from_json_data(
        person_with_mononym_json_data
    )


@pytest_asyncio.fixture(name="person_with_mononym_json_data")
async def fixture_person_with_mononym_json_data(_base_path) -> dict:
    """
    Create a person with mononym json data
    :return: person with mononym json data
    """
    return _person_json_data_from_file(_base_path, "person_with_mononym")


@pytest_asyncio.fixture(name="person_c_with_two_last_names_pydantic_model")
async def fixture_person_c_with_two_last_names_pydantic_model(_base_path) -> Person:
    """
    Create a basic person pydantic model with two last names
    :return: basic person pydantic model with two last names
    """
    return _person_from_json_data(
        _person_json_data_from_file(_base_path, "person_c_with_two_last_names")
    )


@pytest_asyncio.fixture(name="person_d_with_two_memberships_json_data")
async def fixture_person_d_with_two_memberships_json_data(_base_path) -> dict:
    """
    Create a person with two memberships json data
    :return: person with two memberships json data
    """
    return _person_json_data_from_file(_base_path, "person_d_with_two_memberships")


@pytest_asyncio.fixture(name="person_d_with_two_memberships_pydantic_model")
async def fixture_person_d_with_two_memberships_pydantic_model(
        person_d_with_two_memberships_json_data) -> Person:
    """
    Create a person with name in multiple languages pydantic model
    :return: person with name in multiple languages pydantic model
    """
    return _person_from_json_data(person_d_with_two_memberships_json_data)


@pytest_asyncio.fixture(name="person_a_with_invalid_orcid_json_data")
async def fixture_person_a_with_invalid_orcid_json_data(_base_path) -> dict:
    """
    Create a person with invalid orcid json data
    :return: person with invalid orcid json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_orcid")


@pytest_asyncio.fixture(name="person_a_with_invalid_scopus_json_data")
async def fixture_person_a_with_invalid_scopus_json_data(_base_path) -> dict:
    """
    Create a person with invalid orcid json data
    :return: person with invalid orcid json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_scopus_eid")


@pytest_asyncio.fixture(name="person_a_with_invalid_idref_json_data")
async def fixture_person_a_with_invalid_idref_json_data(_base_path) -> dict:
    """
    Create a person with invalid idref json data
    :return: person with invalid idref json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_idref")


@pytest_asyncio.fixture(name="person_a_with_invalid_idhal_s_json_data")
async def fixture_person_a_with_invalid_idhal_s_json_data(_base_path) -> dict:
    """
    Create a person with invalid id_hal_s json data
    :return: person with invalid id_hal_s json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_idhal_s")


@pytest_asyncio.fixture(name="person_a_with_invalid_idhal_i_json_data")
async def fixture_person_a_with_invalid_idhal_i_json_data(_base_path) -> dict:
    """
    Create a person with invalid id_hal_i json data
    :return: person with invalid id_hal_i json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_idhal_i")


@pytest_asyncio.fixture(name="person_a_without_name_json_data")
async def fixture_person_a_without_name_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_a_without_name")


@pytest_asyncio.fixture(name="person_a_without_name_pydantic_model")
async def fixture_person_a_without_name_pydantic_model(
        person_a_without_name_json_data,
) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_a_without_name_json_data)
