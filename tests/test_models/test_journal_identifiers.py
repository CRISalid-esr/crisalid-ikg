import pytest

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier


def test_journal_identifier_creation():
    """
    Given a valid identifier type and value
    When creating a journal identifier
    Then the identifier should be created successfully
    :return:
    """
    identifier = JournalIdentifier(type=JournalIdentifierType.ISSN, value="1234-5678-9101")
    assert identifier.type == JournalIdentifierType.ISSN
    assert identifier.value == "1234-5678-9101"
    assert identifier.uid == "issn-1234-5678-9101"


def test_journal_identifier_type_validation():
    """
    Given an invalid identifier type
    When creating a journal identifier
    Then a ValueError should be raised

    :return:
    """
    with pytest.raises(ValueError):
        JournalIdentifier(type="invalid_type", value="1234-5678-9101")
