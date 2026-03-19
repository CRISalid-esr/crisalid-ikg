from app.models.identifier_types import OrganizationIdentifierType
from app.models.organizations import Organization


def test_create_valid_organization(research_unit_a_json_data):
    """
    Given a valid organization model
    When asked for different field values
    Then the values should be returned correctly
    :param research_unit_a_json_data:
    :return:
    """
    organization = Organization(**research_unit_a_json_data)
    assert len(research_unit_a_json_data["names"]) == 2
    assert len(organization.names) == len(research_unit_a_json_data["names"])

    assert any(
        literal.value == "Laboratoire toto" and literal.language == "fr"
        for literal in organization.names
    )

    assert any(
        literal.value == "Foobar Laboratory" and literal.language == "en"
        for literal in organization.names
    )

    assert len(research_unit_a_json_data["identifiers"]) == 3
    assert len(organization.identifiers) == len(
        research_unit_a_json_data["identifiers"]
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


def test_create_organization_with_duplicate_identifier(
        research_unit_with_duplicate_identifiers_json_data, caplog
):
    """
    Given json organization data with invalid identifier type
    When creating an organization object
    Then a ValueError should be raised

    :param research_unit_with_duplicate_identifiers_json_data:
     json data with invalid identifier type
    :return:
    """
    org = Organization(**research_unit_with_duplicate_identifiers_json_data)
    assert "Duplicate identifier type found" in caplog.text
    assert len(org.identifiers) == 3
    assert any(
        identifier
        for identifier in org.identifiers
        if identifier.type == OrganizationIdentifierType.LOCAL
        and identifier.value == "U153"
    )
    assert any(
        identifier
        for identifier in org.identifiers
        if identifier.type == OrganizationIdentifierType.RNSR
        and identifier.value == "200012133S"
    )
    assert any(
        identifier
        for identifier in org.identifiers
        if identifier.type == OrganizationIdentifierType.ROR
        and identifier.value == "153456"
    )


def test_create_organization_without_name(research_unit_b_without_name_json_data):
    """
    Given json person data with invalid identifier type
    When asked for different field values
    Then the values should be returned correctly

    :param research_unit_b_without_name_json_data: json data with name field empty
    :return:
    """
    organization = Organization(**research_unit_b_without_name_json_data)
    assert len(organization.names) == 0
    assert len(organization.identifiers) == 3
