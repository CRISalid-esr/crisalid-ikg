"""
Integration tests verifying that a Person can be attached via MEMBER_OF
to non-ResearchUnit OrganizationUnit types (e.g. SupportUnit).
"""
import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.organization_unit import OrganizationBase, SupportUnit
from app.models.people import Person


@pytest.mark.asyncio
async def test_person_can_be_member_of_support_unit(
        persisted_support_unit_a_pydantic_model: OrganizationBase,
        person_a_with_support_unit_membership_pydantic_model: Person,
):
    """
    Given a persisted SupportUnit (scientific_services mission)
    And a Person whose membership points to that SupportUnit
    When the person is created
    Then the MEMBER_OF relationship to the SupportUnit should be persisted
    and retrieved correctly.
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao = factory.get_dao(Person)

    # Persist the person
    await person_dao.create(person_a_with_support_unit_membership_pydantic_model)

    # Retrieve by local identifier
    local_identifier = person_a_with_support_unit_membership_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await person_dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )

    assert person_from_db is not None, "Person should exist in the database"
    assert len(person_from_db.memberships) == 1, (
        "Person should have exactly one membership"
    )

    membership = person_from_db.memberships[0]
    assert membership.entity_uid == "local-SP001", (
        "Membership entity_uid should point to the SupportUnit"
    )

    # Also verify the SupportUnit itself has the correct type
    assert isinstance(persisted_support_unit_a_pydantic_model, SupportUnit), (
        "The persisted structure should be a SupportUnit"
    )
