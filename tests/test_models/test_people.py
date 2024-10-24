import pytest

from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


def test_create_valid_person(person_a_json_data):
    """
    Given a valid person model
    When asked for different field values
    Then the values should be returned correctly
    :param person_a_pydantic_model:
    :return:
    """
    person = Person(**person_a_json_data)
    assert len(person.names) == 1
    assert len(person.identifiers) == 2
    assert any(
        name
        for name in person.names
        if any(literal for literal in name.first_names if literal.value == "John")
        and any(literal for literal in name.last_names if literal.value == "Doe")
    )
    assert any(
        identifier
        for identifier in person.identifiers
        if identifier.type == PersonIdentifierType.ORCID
        and identifier.value == "0000-0001-2345-6789"
    )
    assert any(
        identifier
        for identifier in person.identifiers
        if identifier.type == PersonIdentifierType.LOCAL
        and identifier.value == "jdoe@univ-domain.edu"
    )


def test_create_invalid_person(person_a_with_invalid_identifier_type_json_data):
    """
    Given json person data with invalid identifier type
    When creating a person object
    Then a ValueError should be raised

    :param person_a_with_invalid_identifier_type_json_data: json data with invalid identifier type
    :return:
    """
    with pytest.raises(ValueError):
        Person(**person_a_with_invalid_identifier_type_json_data)


def test_create_person_c_with_two_last_names(person_c_with_two_last_names_json_data):
    """
    Given json person data with two last names
    When asked for different field values
    Then the values should be returned correctly
    :param person_a_pydantic_model:
    :return:
    """
    person = Person(**person_c_with_two_last_names_json_data)

    assert len(person.names) == 1
    assert len(person.identifiers) == 2
    assert any(
        name
        for name in person.names
        if any(literal for literal in name.first_names if literal.value == "Jane")
        and any(literal for literal in name.last_names if literal.value == "Mariée")
        and any(literal for literal in name.last_names if literal.value == "Done")
    )
    assert any(
        identifier
        for identifier in person.identifiers
        if identifier.type == PersonIdentifierType.ORCID
        and identifier.value == "0000-0001-2345-6789"
    )
    assert any(
        identifier
        for identifier in person.identifiers
        if identifier.type == PersonIdentifierType.LOCAL
        and identifier.value == "jdone@univ-domain.edu"
    )


def test_create_person_with_mononym(person_with_mononym_json_data):
    """
    Given json person data with a mononym
    When creating a person object
    Then the person object should be created correctly
    :param person_with_mononym_json_data:
    :return:
    """
    person = Person(**person_with_mononym_json_data)
    assert len(person.names) == 1
    assert len(person.identifiers) == 2
    assert any(
        name
        for name in person.names
        if any(literal for literal in name.first_names if literal.value == "Jeanne")
        and not any(literal for literal in name.last_names)
    )


def test_create_person_a_with_name_in_multiple_lng(
        person_a_with_name_in_multiple_lng_json_data,
):
    """
    Given json person data with name in multiple languages
    When creating a person object
    Then the person object should be created correctly
    :param person_a_with_name_in_multiple_lng_json_data:
    :return:
    """
    person = Person(**person_a_with_name_in_multiple_lng_json_data)

    assert len(person.names) == 1
    assert len(person.identifiers) == 2
    assert any(
        name
        for name in person.names
        if any(
            literal
            for literal in name.first_names
            if literal.value == "John" and literal.language == "fr"
        )
        and any(
            literal
            for literal in name.first_names
            if literal.value == "Михаил Александрович" and literal.language == "ru"
        )
        and any(
            literal
            for literal in name.last_names
            if literal.value == "Doe" and literal.language == "fr"
        )
        and any(
            literal
            for literal in name.last_names
            if literal.value == "Бакунин" and literal.language == "ru"
        )
    )


@pytest.mark.parametrize(
    "invalid_identifier_data_fixture",
    [
        "person_a_with_invalid_orcid_json_data",
        "person_a_with_invalid_scopus_json_data",
        "person_a_with_invalid_idref_json_data",
        "person_a_with_invalid_idhal_s_json_data",
        "person_a_with_invalid_idhal_i_json_data"
    ],
    ids=[
        "person_a_with_invalid_orcid_json_data",
        "person_a_with_invalid_scopus_json_data",
        "person_a_with_invalid_idref_json_data",
        "person_a_with_invalid_idhal_s_json_data",
        "person_a_with_invalid_idhal_i_json_data"
    ]
)
def test_create_person_with_invalid_identifier(invalid_identifier_data_fixture, request):
    """
    Given json person data with an invalid identifier type
    When creating a person object
    Then a ValueError should be raised

    :param invalid_identifier_data_fixture: Fixture providing invalid identifier data
    :param request: Pytest request object to get the fixture by name
    :return: None
    """
    # Retrieve the fixture dynamically using the request object
    person_data = request.getfixturevalue(invalid_identifier_data_fixture)

    with pytest.raises(ValueError):
        Person(**person_data)


def test_create_person_a_with_two_orcid(person_a_with_two_orcid_json_data):
    """
    Given json person data with two orcid
    When creating a person object
    Then a ValueError should be raised
    :param person_a_with_two_orcid_json_data: json data with two orcid
    :return:
    """
    with pytest.raises(ValueError):
        Person(**person_a_with_two_orcid_json_data)


def test_create_person_d_with_two_memberships(
        person_d_with_two_memberships_json_data
):
    """
    Given json person data with two memberships
    When asked for different field values
    Then the values should be returned correctly
    :param person_d_with_two_memberships_json_data:
    :return:
    """
    person = Person(**person_d_with_two_memberships_json_data)
    assert len(person_d_with_two_memberships_json_data["memberships"]) == 2
    assert len(person.memberships) == len(person_d_with_two_memberships_json_data["memberships"])
    expected_uids = ['local-U123', 'local-U153']
    uids = list(map(lambda m: m.entity_uid, person.memberships))
    assert sorted(uids) == sorted(expected_uids)


def test_create_person_a_without_name(person_a_without_name_json_data):
    """
    Given json person data with invalid identifier type
    When asked for different field values
    Then the values should be returned correctly

    :param person_a_without_name_json_data: json data with name field empty
    :return:
    """
    person = Person(**person_a_without_name_json_data)
    assert len(person.names) == 0
    assert len(person.identifiers) == 2


def test_create_person_with_implicit_local_membership_identifier(
        person_a_with_implicit_local_membership_identifier_json_data
) -> None:
    """
    Given json person data with a membership entity uid without the "local" prefix
    When creating a person object
    Then the person object should be created correctly
    :param person_a_with_implicit_local_membership_identifier_json_data:
    :return:
    """
    person = Person(**person_a_with_implicit_local_membership_identifier_json_data)
    assert len(person.names) == 1
    assert len(person.memberships) == 1
    assert person.memberships[0].entity_uid == \
           "local-U123"  # pylint: disable=unsubscriptable-object
