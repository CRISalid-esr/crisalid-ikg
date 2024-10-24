from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType, OrganizationIdentifierType
from app.models.people import Person
from app.models.research_structures import ResearchStructure

async def test_update_people_and_structure(
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        persisted_research_structure_b_pydantic_model: ResearchStructure,
        persisted_person_a_pydantic_model: Person,
        person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model: Person,
        research_structure_a_with_name_acronym_description_street_ror_added_italian_description_name_added_pydantic_model: ResearchStructure
):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param person_d_with_two_memberships_pydantic_model:
    :param persisted_research_structure_a_pydantic_model:
    :return:
    """

    async def assert_identifiers_match(updated_object, pydantic_object):
        assert len(updated_object.identifiers) == len(pydantic_object.identifiers)
        assert all(
            any(
                updated.type == new.type and updated.value == new.value
                for updated in updated_object.identifiers
            )
            for new in pydantic_object.identifiers
        )

    async def assert_names_match(updated_object, pydantic_object):
        fields = ("first_names", "last_names") if isinstance(updated_object, Person) else (
            "value", "language")
        assert len(updated_object.names) == len(pydantic_object.names)
        assert all(
            any(
                getattr(updated_name, fields[0]) == getattr(new_name, fields[0]) and getattr(
                    updated_name, fields[1]) == getattr(new_name, fields[1])
                for updated_name in updated_object.names
            )
            for new_name in pydantic_object.names
        )

    async def assert_memberships_match(updated_object, pydantic_object):
        assert len(updated_object.memberships) == len(pydantic_object.memberships)
        assert all(
            any(membership.entity_uid == updated_membership.entity_uid
                for updated_membership in updated_object.memberships
                )
            for membership in pydantic_object.memberships
        )

    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao = factory.get_dao(Person)
    people_local_identifier = persisted_person_a_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )

    structure_dao = factory.get_dao(ResearchStructure)
    structure_local_identifier = persisted_research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL
    )

    person_from_db = await person_dao.find_by_identifier(
        people_local_identifier.type, people_local_identifier.value
    )
    assert person_from_db
    await assert_memberships_match(person_from_db, persisted_person_a_pydantic_model)
    await assert_names_match(person_from_db, persisted_person_a_pydantic_model)

    assert sum(len(name.first_names) for name in person_from_db.names) == 1
    assert not any(
        identifier.type == PersonIdentifierType.ID_HAL_S
        for identifier in person_from_db.identifiers
    )
    # Update persisted person a
    await person_dao.update(
        person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model)
    updated_person_from_db = await person_dao.find_by_identifier(
        people_local_identifier.type, people_local_identifier.value
    )
    assert updated_person_from_db
    await assert_memberships_match(
        updated_person_from_db,
        person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model
    )

    await assert_names_match(
        updated_person_from_db,
        person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model
    )

    await assert_identifiers_match(
        updated_person_from_db,
        person_a_with_different_name_new_hal_identifier_and_membership_pydantic_model
    )

    # update structure a
    await structure_dao.update(
        research_structure_a_with_name_acronym_description_street_ror_added_italian_description_name_added_pydantic_model)
    updated_structure_from_db = await structure_dao.find_by_identifier(
        structure_local_identifier.type, structure_local_identifier.value
    )
    assert updated_structure_from_db
    await assert_identifiers_match(
        updated_structure_from_db,
        research_structure_a_with_name_acronym_description_street_ror_added_italian_description_name_added_pydantic_model
    )
    await assert_names_match(
        updated_structure_from_db,
        research_structure_a_with_name_acronym_description_street_ror_added_italian_description_name_added_pydantic_model
    )
