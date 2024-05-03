import pytest

from app.models.agent_identifiers import PersonIdentifier
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


@pytest.fixture
def valid_person_data():
    return {
        "first_names": ["John"],
        "last_names": ["Doe"],
        "alternative_names": ["Johnny"],
        "identifiers": [
            {"type": PersonIdentifierType.ORCID, "value": "0000-0000-0000-0000"}
        ]
    }


@pytest.fixture
def invalid_person_data():
    return {
        "first_names": ["John"],
        "last_names": ["Doe"],
        "alternative_names": ["Johnny"],
        "identifiers": [
            {"type": "InvalidIdentifier", "value": "0000-0000-0000-0000"}
        ]
    }


def test_create_valid_person(valid_person_data):
    person = Person(**valid_person_data)
    assert person
    assert person.first_names == valid_person_data["first_names"]
    assert person.last_names == valid_person_data["last_names"]
    assert person.alternative_names == valid_person_data["alternative_names"]


def test_create_invalid_person(invalid_person_data):
    with pytest.raises(ValueError):
        Person(**invalid_person_data)
