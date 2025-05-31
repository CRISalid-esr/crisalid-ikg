import pytest_asyncio

from app.models.people import Person
from app.services.people.people_service import PeopleService
from tests.fixtures.common import _person_from_json_data, _person_json_data_from_file


@pytest_asyncio.fixture(name="persisted_person_a_pydantic_model")
async def fixture_persisted_person_a_pydantic_model(person_a_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic persisted person pydantic model
    """
    people_service: PeopleService = PeopleService()
    await people_service.create_person(person_a_pydantic_model)
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


# keep raw json as person_a_json_data is modifier by "before" pydantic validators
@pytest_asyncio.fixture(name="raw_person_a_json_data")
async def fixture_raw_person_a_json_data(_base_path) -> dict:
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


@pytest_asyncio.fixture(name="persisted_person_b_pydantic_model")
async def fixture_persisted_person_b_pydantic_model(
        person_b_with_two_names_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic persisted person pydantic model
    """
    people_service: PeopleService = PeopleService()
    await people_service.create_person(person_b_with_two_names_pydantic_model)
    return person_b_with_two_names_pydantic_model


@pytest_asyncio.fixture(name="person_b_with_two_names_pydantic_model")
async def fixture_person_b_with_two_names_pydantic_model(_base_path) -> Person:
    """
    Create a basic person pydantic model with two names
    :return: basic person pydantic model with two names
    """
    return _person_from_json_data(
        _person_json_data_from_file(_base_path, "person_b_with_two_names")
    )


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


@pytest_asyncio.fixture(name="person_d_with_empty_membership_entity_uid_json_data")
async def fixture_pperson_d_with_empty_membership_entity_uid_json_data(_base_path) -> dict:
    """
    Create a person with empty membership entity uid json data
    :return: person with empty membership entity uid json data
    """
    return _person_json_data_from_file(_base_path, "person_d_with_empty_membership_entity_uid")


@pytest_asyncio.fixture(name="person_d_with_two_memberships_pydantic_model")
async def fixture_person_d_with_two_memberships_pydantic_model(
        person_d_with_two_memberships_json_data) -> Person:
    """
    Create a person with name in multiple languages pydantic model
    :return: person with name in multiple languages pydantic model
    """
    return _person_from_json_data(person_d_with_two_memberships_json_data)


@pytest_asyncio.fixture(name="person_a_with_two_employments_pydantic_model")
async def fixture_person_a_with_two_employments_pydantic_model(
        person_a_with_two_employments_json_data) -> Person:
    """
    Create a person with two employments pydantic model
    :return: person with two employments pydantic model
    """
    return _person_from_json_data(person_a_with_two_employments_json_data)


@pytest_asyncio.fixture(name="person_a_with_two_employments_json_data")
async def fixture_person_a_with_two_employments_json_data(_base_path) -> dict:
    """
    Create a person with two employments json data
    :return: person with two employments json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_two_employments")


@pytest_asyncio.fixture(name="person_a_with_invalid_employment_position_pydantic_model")
async def fixture_person_a_with_invalid_employment_position_pydantic_model(
        person_a_with_invalid_employment_position_json_data) -> Person:
    """
    Create a person with invalid employment position pydantic model
    :return: person with invalid employment position pydantic model
    """
    return _person_from_json_data(person_a_with_invalid_employment_position_json_data)


@pytest_asyncio.fixture(name="person_a_with_invalid_employment_position_json_data")
async def fixture_person_a_with_invalid_employment_position_json_data(_base_path) -> dict:
    """
    Create a person with invalid employment position json data
    :param _base_path:
    :return:
    """
    return _person_json_data_from_file(_base_path, "person_a_with_invalid_employment_position")


@pytest_asyncio.fixture(name="person_a_with_employment_without_position_pydantic_model")
async def fixture_person_a_with_employment_without_position_pydantic_model(
        person_a_with_employment_without_position_json_data) -> Person:
    """
    Create a person with employment without position pydantic model
    :return: person with employment without position pydantic model
    """
    return _person_from_json_data(person_a_with_employment_without_position_json_data)


@pytest_asyncio.fixture(name="person_a_with_employment_without_position_json_data")
async def fixture_person_a_with_employment_without_position_json_data(_base_path) -> dict:
    """
    Create a person with employment without position json data
    :return: person with employment without position json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_employment_without_position")


@pytest_asyncio.fixture(name="person_a_with_different_employment_pydantic_model")
async def fixture_person_a_with_different_employment_pydantic_model(
        person_a_with_different_employment_json_data) -> Person:
    """
    Create a person with different employment pydantic model
    :return: person with different employment pydantic model
    """
    return _person_from_json_data(person_a_with_different_employment_json_data)


@pytest_asyncio.fixture(name="person_a_with_different_employment_json_data")
async def fixture_person_a_with_different_employment_json_data(_base_path) -> dict:
    """
    Create a person with different employment json data
    :return: person with different employment json data
    """
    return _person_json_data_from_file(_base_path, "person_a_with_different_employment")


@pytest_asyncio.fixture(name="person_a_with_different_employment_position_pydantic_model")
async def fixture_person_a_with_different_employment_position_pydantic_model(
        person_a_with_different_employment_position_json_data) -> Person:
    """
    Create a person with different employment position pydantic model
    :return: person with different employment position pydantic model
    """
    return _person_from_json_data(person_a_with_different_employment_position_json_data)


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


@pytest_asyncio.fixture(
    name="person_a_with_different_name_new_hal_identifier_and_membership_json_data")
async def fixture_person_a_with_different_name_new_hal_identifier_and_membership_json_data(
        _base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(
        _base_path, "person_a_with_different_name_new_hal_identifier_and_membership"
    )


@pytest_asyncio.fixture(
    name="person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model")
async def fixture_person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model(
        person_a_with_different_name_new_hal_identifier_and_membership_json_data,
) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(
        person_a_with_different_name_new_hal_identifier_and_membership_json_data)


@pytest_asyncio.fixture(name="persisted_person_d_pydantic_model")
async def fixture_persisted_person_d_pydantic_model(person_d_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic persisted person pydantic model
    """
    people_service: PeopleService = PeopleService()
    await people_service.create_person(person_d_pydantic_model)
    return person_d_pydantic_model


@pytest_asyncio.fixture(name="person_d_pydantic_model")
async def fixture_person_d_pydantic_model(person_d_json_data) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_d_json_data)


@pytest_asyncio.fixture(name="person_d_json_data")
async def fixture_person_d_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_d")


@pytest_asyncio.fixture(name="persisted_person_e_pydantic_model")
async def fixture_persisted_person_e_pydantic_model(person_e_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic persisted person pydantic model
    """
    people_service: PeopleService = PeopleService()
    await people_service.create_person(person_e_pydantic_model)
    return person_e_pydantic_model


@pytest_asyncio.fixture(name="person_e_pydantic_model")
async def fixture_person_e_pydantic_model(person_e_json_data) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_e_json_data)


@pytest_asyncio.fixture(name="person_e_json_data")
async def fixture_person_e_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_e")


@pytest_asyncio.fixture(name="persisted_person_f_pydantic_model")
async def fixture_persisted_person_f_pydantic_model(person_f_pydantic_model) -> Person:
    """
    Create a basic persisted person pydantic model
    :return: basic person pydantic model
    """
    people_service: PeopleService = PeopleService()
    await people_service.create_person(person_f_pydantic_model)
    return person_f_pydantic_model


@pytest_asyncio.fixture(name="person_f_pydantic_model")
async def fixture_person_f_pydantic_model(person_f_json_data) -> Person:
    """
    Create a basic person pydantic model
    :return: basic person pydantic model
    """
    return _person_from_json_data(person_f_json_data)


@pytest_asyncio.fixture(name="person_f_json_data")
async def fixture_person_f_json_data(_base_path) -> dict:
    """
    Create a basic person json data
    :return: basic person json data
    """
    return _person_json_data_from_file(_base_path, "person_f")
