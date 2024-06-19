import pytest

from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


@pytest.fixture
def valid_person_data():
    return {
        "names": [
            {
                "first_names": [
                    "John"
                ],
                "family_names": [
                    "Doe"
                ],
                "other_names": [
                    "Johnny"
                ]
            }
        ],
        "identifiers": [
            {
                "type": "ORCID",
                "value": "0000-0001-2345-6789"
            },
            {
                "type": "local",
                "value": "jdoe@univ-paris1.fr"
            }
        ]
    }


@pytest.fixture
def invalid_person_data():
    # wrong identifier type "InvalidIdentifier"
    return {
        "names": [
            {
                "first_names": [
                    "John"
                ],
                "family_names": [
                    "Doe"
                ],
                "other_names": [
                    "Johnny"
                ]
            }
        ],
        "identifiers": [
            {
                "type": "InvalidIdentifier",
                "value": "0000-0001-2345-6789"
            },
            {
                "type": "local",
                "value": "jdoe@univ-paris1.fr"
            }
        ]
    }


def test_create_valid_person(valid_person_data):
    person = Person(**valid_person_data)
    assert person
    assert len(person.names) == 1
    assert len(person.identifiers) == 2
    assert any(
        name for name in person.names if "John" in name.first_names and "Doe" in name.family_names and "Johnny" in name.other_names
    )
    assert any(
        identifier for identifier in person.identifiers if identifier.type == PersonIdentifierType.ORCID and identifier.value == "0000-0001-2345-6789"
    )
    assert any(
        identifier for identifier in person.identifiers if identifier.type == PersonIdentifierType.LOCAL and identifier.value == "jdoe@univ-paris1.fr"
    )



def test_create_invalid_person(invalid_person_data):
    with pytest.raises(ValueError):
        Person(**invalid_person_data)
