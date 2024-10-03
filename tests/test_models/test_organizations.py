from app.models.identifier_types import OrganizationIdentifierType
from app.models.organizations import Organization


def test_create_valid_organization(research_structure_json_data):
    """
    Given a valid organization model
    When asked for different field values
    Then the values should be returned correctly
    :param research_structure_json_data:
    :return:
    """
    organization = Organization(**research_structure_json_data)
    assert len(research_structure_json_data["names"]) == 2
    assert len(organization.names) == len(research_structure_json_data["names"])

    assert any(
        literal.value == "Laboratoire toto" and literal.language == "fr"
        for literal in organization.names
    )

    assert any(
        literal.value == "Foobar Laboratory" and literal.language == "en"
        for literal in organization.names
    )

    assert len(research_structure_json_data["identifiers"]) == 3
    assert len(organization.identifiers) == len(
        research_structure_json_data["identifiers"]
    )
    assert any(
        identifier.value == "U123" and identifier.type == OrganizationIdentifierType.LOCAL
        for identifier in organization.identifiers
    )
    assert any(
        identifier.value == "200012123S" and identifier.type == OrganizationIdentifierType.RNSR
        for identifier in organization.identifiers
    )
    assert any(
        identifier.value == "123456" and identifier.type == OrganizationIdentifierType.ROR
        for identifier in organization.identifiers
    )
