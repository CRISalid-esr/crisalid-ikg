from typing import cast

import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.institution_dao import InstitutionDAO
from app.models.identifier_types import OrganizationIdentifierType
from app.models.institution import Institution
from app.models.people import Person
from app.models.research_structures import ResearchStructure
from app.services.people.people_service import PeopleService


async def test_create_person(
        person_a_pydantic_model: Person,
        persisted_research_structure_a_pydantic_model  # pylint: disable=unused-argument
) -> None:
    """
    Given a basic person pydantic model
    When the person is added to the graph
    Then the person can be read from the graph
    :param person_a_pydantic_model:
    :return:
    """
    service = PeopleService()
    await service.create_person(person_a_pydantic_model)
    fetched_person = await service.get_person(person_a_pydantic_model.uid)
    assert fetched_person.uid == person_a_pydantic_model.uid
    assert len(fetched_person.identifiers) == len(person_a_pydantic_model.identifiers)
    for identifier in person_a_pydantic_model.identifiers:
        assert any(
            fetched_identifier.type == identifier.type
            and fetched_identifier.value == identifier.value
            for fetched_identifier in fetched_person.identifiers
        )
    assert len(fetched_person.names) == len(person_a_pydantic_model.names)
    assert len(person_a_pydantic_model.memberships) == 1
    assert len(fetched_person.memberships) == len(person_a_pydantic_model.memberships)
    assert len(person_a_pydantic_model.memberships[0].research_structure.identifiers) == 1
    assert len(fetched_person.memberships[0].research_structure.identifiers) == len(
        person_a_pydantic_model.memberships[0].research_structure.identifiers
    )
    for fetched_membership in fetched_person.memberships:
        for fetched_identifier in fetched_membership.research_structure.identifiers:
            assert any(
                identifier.type == fetched_identifier.type
                and identifier.value == fetched_identifier.value
                for membership in person_a_pydantic_model.memberships
                for identifier in membership.research_structure.identifiers
            )
    assert len(person_a_pydantic_model.employments) == 1
    assert len(fetched_person.employments) == len(person_a_pydantic_model.employments)
    assert len(person_a_pydantic_model.employments[0].institution.identifiers) == 1
    assert len(fetched_person.employments[0].institution.identifiers) == len(
        person_a_pydantic_model.employments[0].institution.identifiers
    )
    # Only the uai identifier is available
    # as it is deduced from the institution uid
    assert any(
        identifier.type == OrganizationIdentifierType.UAI
        and identifier.value == fetched_identifier.value
        for fetched_employment in fetched_person.employments
        for fetched_identifier in fetched_employment.institution.identifiers
        for employment in person_a_pydantic_model.employments
        for identifier in employment.institution.identifiers
    )


async def test_create_person_a_without_name(
        person_a_without_name_json_data: dict
) -> None:
    """
    Given a person without name pydantic model
    When the person is added to the graph
    Then the person can be read from the graph
    :param person_a_without_name_pydantic_model:
    :return:
    """
    service = PeopleService()
    with pytest.raises(ValueError) as exc_info:
        person_a_without_name_pydantic_model = Person(**person_a_without_name_json_data)
        await service.create_person(person_a_without_name_pydantic_model)
    assert ("Either a display_name or at least one person name "
            "with a last name or first name must be provided.") in str(
        exc_info.value)


async def test_update_person_membership(
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        persisted_research_structure_b_pydantic_model: ResearchStructure,
        persisted_person_a_pydantic_model: Person,
        person_a_with_different_membership_pydantic_model: Person,
) -> None:
    """
    Given an existing person pydantic model
    When the person membership is updated
    Then the person can be read from the graph with updated membership
    :param person_a_pydantic_model:
    :return:
    """
    service = PeopleService()
    fetched_person = await service.get_person(persisted_person_a_pydantic_model.uid)
    assert fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(fetched_person.memberships) == 1
    assert any(
        membership
        for membership in fetched_person.memberships
        if membership.entity_uid == persisted_research_structure_a_pydantic_model.uid
    )
    await service.update_person(person_a_with_different_membership_pydantic_model)
    updated_fetched_person = await service.get_person(
        persisted_person_a_pydantic_model.uid
    )
    assert updated_fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(updated_fetched_person.memberships) == len(fetched_person.memberships)
    assert updated_fetched_person.memberships != fetched_person.memberships
    assert any(
        membership
        for membership in updated_fetched_person.memberships
        if membership.entity_uid
        == persisted_research_structure_b_pydantic_model.uid
    )


async def test_update_person_employment(
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        person_a_with_different_employment_pydantic_model: Person,
) -> None:
    """
    Given an existing person pydantic model
    When the person employments are updated
    Then the person can be read from the graph with updated employments
    :param person_a_pydantic_model:
    :return:
    """
    service = PeopleService()
    settings = get_app_settings()
    institution_dao = cast(
        InstitutionDAO,
        AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(Institution)
    )
    fetched_person = await service.get_person(persisted_person_a_pydantic_model.uid)
    assert fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(fetched_person.employments) == 1
    assert (fetched_person.employments[0].entity_uid ==
            persisted_person_a_pydantic_model.employments[0].entity_uid)
    assert (fetched_person.employments[0].institution.identifiers[0].value ==
            persisted_person_a_pydantic_model.employments[
                0].institution.identifiers[0].value)
    old_institution = await institution_dao.get(fetched_person.employments[0].institution.uid)
    assert old_institution.uid == fetched_person.employments[0].institution.uid
    assert len(old_institution.identifiers) == 5
    assert any(
        identifier
        for identifier in old_institution.identifiers
        if identifier.value == fetched_person.employments[0].institution.identifiers[0].value
    )
    assert any(
        name
        for name in old_institution.names
        if name.value == "International University of the Côte d'Azur"
    )
    assert any(
        name
        for name in old_institution.names
        if name.value == "Université Internationale de la Côte d'Azur"
    )
    assert any(
        identifier
        for identifier in old_institution.identifiers
        if identifier.value == "0751818J"
        and identifier.type == OrganizationIdentifierType.UAI
    )
    assert any(
        identifier
        for identifier in old_institution.identifiers
        if identifier.value == "067431289"
        and identifier.type == OrganizationIdentifierType.IDREF
    )
    assert any(
        identifier
        for identifier in old_institution.identifiers
        if
        identifier.value == "28574391600014"
        and identifier.type == OrganizationIdentifierType.SIRET
    )
    assert any(
        identifier
        for identifier in old_institution.identifiers
        if identifier.value == "Q3338765"
        and identifier.type == OrganizationIdentifierType.WIKIDATA
    )

    await service.update_person(person_a_with_different_employment_pydantic_model)
    updated_fetched_person = await service.get_person(
        persisted_person_a_pydantic_model.uid
    )

    assert updated_fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(updated_fetched_person.employments) == len(
        person_a_with_different_employment_pydantic_model.employments)
    assert updated_fetched_person.employments != fetched_person.employments
    assert any(
        employment
        for employment in updated_fetched_person.employments
        if employment.entity_uid == person_a_with_different_employment_pydantic_model.employments[
            0].entity_uid
    )
    assert any(
        employment
        for employment in updated_fetched_person.employments
        if employment.institution.identifiers[0].value ==
        person_a_with_different_employment_pydantic_model.employments[
            0].institution.identifiers[0].value
    )
    new_institution = await institution_dao.get(
        updated_fetched_person.employments[0].institution.uid
    )
    assert new_institution.uid == updated_fetched_person.employments[0].institution.uid
    assert len(new_institution.identifiers) == 5
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == updated_fetched_person.employments[0].institution.identifiers[
            0].value
    )
    assert any(
        name
        for name in new_institution.names
        if name.value == 'Université de Nouvelles Sciences et Technologies'
    )
    assert any(
        name
        for name in new_institution.names
        if name.value == 'New Science and Technology University'
    )
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == '0833945M'
        and identifier.type == OrganizationIdentifierType.UAI
    )
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == '048762134'
        and identifier.type == OrganizationIdentifierType.IDREF
    )
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == '209845672'
        and identifier.type == OrganizationIdentifierType.SIREN
    )
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == '20984567200017'
        and identifier.type == OrganizationIdentifierType.SIRET
    )
    assert any(
        identifier
        for identifier in new_institution.identifiers
        if identifier.value == 'Q1112345'
        and identifier.type == OrganizationIdentifierType.WIKIDATA
    )


async def test_update_person_employment_position(
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        person_a_with_different_employment_pydantic_model: Person,
) -> None:
    """
    Given an existing person pydantic model
    When the person employment position is updated
    Then the person can be read from the graph with updated employment position
    :param person_a_pydantic_model:
    :return:
    """
    service = PeopleService()
    fetched_person = await service.get_person(persisted_person_a_pydantic_model.uid)
    assert fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(fetched_person.employments) == 1
    assert (fetched_person.employments[0].entity_uid ==
            persisted_person_a_pydantic_model.employments[0].entity_uid)
    assert (fetched_person.employments[0].institution.identifiers[0].value ==
            persisted_person_a_pydantic_model.employments[
                0].institution.identifiers[0].value)
    assert (fetched_person.employments[0].position.code ==
            persisted_person_a_pydantic_model.employments[0].position.code)
    await service.update_person(person_a_with_different_employment_pydantic_model)
    updated_fetched_person = await service.get_person(
        persisted_person_a_pydantic_model.uid
    )
    assert updated_fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(updated_fetched_person.employments) == len(
        person_a_with_different_employment_pydantic_model.employments)
    assert any(
        employment
        for employment in updated_fetched_person.employments
        if employment.entity_uid == person_a_with_different_employment_pydantic_model.employments[
            0].entity_uid
    )
    assert any(
        employment
        for employment in updated_fetched_person.employments
        if employment.institution.identifiers[0].value ==
        person_a_with_different_employment_pydantic_model.employments[
            0].institution.identifiers[0].value
    )
    assert any(
        employment
        for employment in updated_fetched_person.employments
        if employment.position.code ==
        person_a_with_different_employment_pydantic_model.employments[0].position.code
    )
