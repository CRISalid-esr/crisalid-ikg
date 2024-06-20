import pytest

from app.models.agent_identifiers import PersonIdentifier
from app.models.identifier_types import PersonIdentifierType


def test_person_identifier_creation():
    """
    Given a valid identifier type and value
    When creating a person identifier
    Then the identifier should be created successfully
    :return:
    """
    identifier = PersonIdentifier(type=PersonIdentifierType.ORCID, value="1234-5678-9101")
    assert identifier.type == PersonIdentifierType.ORCID
    assert identifier.value == "1234-5678-9101"


def test_person_identifier_type_validation():
    """
    Given an invalid identifier type
    When creating a person identifier
    Then a ValueError should be raised

    :return:
    """
    with pytest.raises(ValueError):
        PersonIdentifier(type="invalid_type", value="1234-5678-9101")
