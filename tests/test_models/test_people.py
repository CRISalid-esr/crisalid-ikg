import pytest

from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


def test_create_valid_person(basic_person_pydantic_model):
    """
    Given a valid person model
    When asked for different field values
    Then the values should be returned correctly
    :param basic_person_pydantic_model:
    :return:
    """
    assert basic_person_pydantic_model
    assert len(basic_person_pydantic_model.names) == 1
    assert len(basic_person_pydantic_model.identifiers) == 2
    assert any(
        name for name in basic_person_pydantic_model.names if
        any(
            literal for literal in name.first_names if literal.value == "John"
        ) and any(
            literal for literal in name.last_names if literal.value == "Doe"
        )
    )
    assert any(
        identifier for identifier in basic_person_pydantic_model.identifiers if
        identifier.type == PersonIdentifierType.ORCID and identifier.value == "0000-0001-2345-6789"
    )
    assert any(
        identifier for identifier in basic_person_pydantic_model.identifiers if
        identifier.type == PersonIdentifierType.LOCAL and identifier.value == "jdoe@univ-paris1.fr"
    )


def test_create_invalid_person(person_with_invalid_identifier_type_json_data):
    """
    Given json person data with invalid identifier type
    When creating a person object
    Then a ValueError should be raised

    :param person_with_invalid_identifier_type_json_data: json data with invalid identifier type
    :return:
    """
    with pytest.raises(ValueError):
        Person(**person_with_invalid_identifier_type_json_data)
