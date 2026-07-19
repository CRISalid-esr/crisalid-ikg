import datetime

import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import OrganizationIdentifierType, PersonIdentifierType
from app.models.organization_unit import OrganizationBase
from app.models.people import Person
from app.services.organizations.institution_service import InstitutionService
from app.services.people.people_service import PeopleService


async def test_create_person(
        person_a_pydantic_model: Person,
        persisted_research_unit_a_pydantic_model  # pylint: disable=unused-argument
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
    assert fetched_person.memberships[0].entity_uid == person_a_pydantic_model.memberships[0].entity_uid
    assert len(person_a_pydantic_model.employments) == 1
    assert len(fetched_person.employments) == len(person_a_pydantic_model.employments)
    assert fetched_person.employments[0].entity_uid == person_a_pydantic_model.employments[0].entity_uid


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
        persisted_research_unit_a_pydantic_model: OrganizationBase,
        persisted_research_unit_b_pydantic_model: OrganizationBase,
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
        if membership.entity_uid == persisted_research_unit_a_pydantic_model.uid
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
        == persisted_research_unit_b_pydantic_model.uid
    )

async def test_update_person_identifiers_with_authentication(
        persisted_person_a_orcid_hal_authenticated_pydantic_model: Person,
        person_a_with_hal_pydantic_model:Person
) -> None:
    """
    Given an existing person pydantic model
    When the person membership is updated
    Then the person can be read from the graph with updated membership
    :param person_a_pydantic_model:
    :return:
    """
    service = PeopleService()
    fetched_person = await service.get_person(
        persisted_person_a_orcid_hal_authenticated_pydantic_model.uid)
    assert fetched_person.uid == persisted_person_a_orcid_hal_authenticated_pydantic_model.uid
    assert all(
        identifier.authenticated is True
        for identifier in fetched_person.identifiers
        if identifier.type.value in {"idhals", "orcid"}
    )

    new_person = person_a_with_hal_pydantic_model.copy()
    new_person.uid = fetched_person.uid
    assert all(
        identifier.authenticated is False
        for identifier in new_person.identifiers
        if identifier.type.value in {"idhals", "orcid"}
    )

    await service.update_person(new_person)
    updated_fetched_person = await service.get_person(
        persisted_person_a_orcid_hal_authenticated_pydantic_model.uid
    )
    assert (updated_fetched_person.uid ==
            persisted_person_a_orcid_hal_authenticated_pydantic_model.uid)
    assert all(
        identifier.authenticated is True
        for identifier in updated_fetched_person.identifiers
        if identifier.type.value in {"idhals", "orcid"}
    )
    actual_authentication_date = "2025-08-25T06:17:28.243Z"
    assert all(identifier.authentication_date ==
            datetime.datetime.fromisoformat(actual_authentication_date.replace("Z", "+00:00"))
            for identifier in updated_fetched_person.identifiers
            if identifier.type.value in {"idhals", "orcid"}
            )


async def test_update_person_preserves_validated_idref(
        persisted_person_a_with_idref_pydantic_model: Person,
) -> None:
    """
    Given a person whose idref has been validated
    When a people-update message re-sends the same idref as non-validated (directory sync)
    Then the validated flag must be preserved (not downgraded/deleted),
        just as authenticated identifiers are preserved.
    """
    person_uid = "local-jdoe_with_idref@univ-domain.edu"
    service = PeopleService()

    # validate the idref
    await service.confirm_identifier(
        person_uid, PersonIdentifierType.IDREF.value, "123456789",
        False, "2025-08-26T06:17:28.243Z")

    validated_person = await service.get_person(person_uid)
    idref_identifier = next(
        (id for id in validated_person.identifiers if
         id.type.value == PersonIdentifierType.IDREF.value), None
    )
    assert idref_identifier.validated is True

    # simulate a directory people-update that re-sends the idref as non-validated
    incoming_person = persisted_person_a_with_idref_pydantic_model.copy()
    incoming_person.uid = person_uid
    assert all(identifier.validated is False for identifier in incoming_person.identifiers)

    await service.update_person(incoming_person)

    updated_person = await service.get_person(person_uid)
    idref_identifier = next(
        (id for id in updated_person.identifiers if
         id.type.value == PersonIdentifierType.IDREF.value), None
    )
    assert idref_identifier is not None
    assert idref_identifier.value == "123456789"
    assert idref_identifier.validated is True


async def test_update_person_employment(
        persisted_research_unit_a_pydantic_model: OrganizationBase,
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
    org_unit_dao = AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(OrganizationBase)
    fetched_person = await service.get_person(persisted_person_a_pydantic_model.uid)
    assert fetched_person.uid == persisted_person_a_pydantic_model.uid
    assert len(fetched_person.employments) == 1
    assert (fetched_person.employments[0].entity_uid ==
            persisted_person_a_pydantic_model.employments[0].entity_uid)
    old_institution = await org_unit_dao.get(fetched_person.employments[0].entity_uid)
    assert old_institution.uid == fetched_person.employments[0].entity_uid
    assert len(old_institution.identifiers) >= 1
    assert any(
        ll for ll in old_institution.long_labels
        if ll.value == "International University of the Côte d'Azur"
    )
    assert any(
        ll for ll in old_institution.long_labels
        if ll.value == "Université Internationale de la Côte d'Azur"
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
        if identifier.value == "28574391600014"
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
    new_institution = await org_unit_dao.get(
        updated_fetched_person.employments[0].entity_uid
    )
    assert new_institution.uid == updated_fetched_person.employments[0].entity_uid
    assert len(new_institution.identifiers) >= 1
    assert any(
        ll for ll in new_institution.long_labels
        if ll.value == 'Université de Nouvelles Sciences et Technologies'
    )
    assert any(
        ll for ll in new_institution.long_labels
        if ll.value == 'New Science and Technology University'
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
        persisted_research_unit_a_pydantic_model: OrganizationBase,
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
        if employment.position.code ==
        person_a_with_different_employment_pydantic_model.employments[0].position.code
    )


def _get_identifier(person: Person, identifier_type: PersonIdentifierType):
    return next(
        (id for id in person.identifiers if id.type == identifier_type), None
    )


async def test_add_identifier_authenticated(
        persisted_person_a_no_orcid_no_hal_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with no orcid identifier
    When an authenticated orcid is added
    Then the identifier is created authenticated and validated
    """
    person_uid = "local-jdoe_no_orcid@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.add_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                 "0000-0001-2345-6789", True, timestamp)

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier.value == "0000-0001-2345-6789"
    assert orcid_identifier.authenticated is True
    assert orcid_identifier.validated is True
    assert orcid_identifier.authentication_date == datetime.datetime.fromisoformat(
        timestamp.replace("Z", "+00:00"))


async def test_add_identifier_manual(
        persisted_person_a_no_orcid_no_hal_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with no idhals identifier
    When an idhals is added manually (no authentication)
    Then the identifier is created validated but not authenticated
    """
    person_uid = "local-jdoe_no_orcid@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.add_identifier(person_uid, PersonIdentifierType.IDHALS.value,
                                 "john-doe", False, timestamp)

    person = await service.get_person(person_uid)
    hal_identifier = _get_identifier(person, PersonIdentifierType.IDHALS)
    assert hal_identifier.value == "john-doe"
    assert hal_identifier.validated is True
    assert hal_identifier.authenticated is False
    assert hal_identifier.authentication_date is None


async def test_add_identifier_idref_never_authenticated(
        persisted_person_a_no_orcid_no_hal_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with no idref identifier
    When an idref is added, even with the authenticated flag set
    Then the identifier is created validated only (idref has no authentication process)
    """
    person_uid = "local-jdoe_no_orcid@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.add_identifier(person_uid, PersonIdentifierType.IDREF.value,
                                 "123456789", True, timestamp)

    person = await service.get_person(person_uid)
    idref_identifier = _get_identifier(person, PersonIdentifierType.IDREF)
    assert idref_identifier.value == "123456789"
    assert idref_identifier.validated is True
    assert idref_identifier.authenticated is False
    assert idref_identifier.authentication_date is None


async def test_add_identifier_existing_type_rejected(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with an orcid identifier
    When another orcid is added
    Then the add is rejected (remove before add) and the existing identifier is unchanged
    """
    person_uid = "local-jdoe@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    with pytest.raises(ValueError):
        await service.add_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                     "0000-0001-2345-4321", False, timestamp)

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier.value == "0000-0001-2345-6789"
    assert orcid_identifier.validated is False
    assert orcid_identifier.authenticated is False


async def test_add_identifier_detaches_external_owner(
        persisted_person_a_no_orcid_no_hal_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an external person owning an orcid AgentIdentifier
    When the same orcid is added to an internal person
    Then the external HAS_IDENTIFIER edge is detached (one owner per identifier)
        and the external person survives with its other data
    """
    person_uid = "local-jdoe_no_orcid@univ-domain.edu"
    orcid_value = "0000-0001-2345-6789"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    external_person = Person(
        uid="scanr-test-external-jdoe",
        display_name="J. Doe",
        external=True,
        names=[],
        identifiers=[]
    )
    await service.create_person(external_person)
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao = factory.get_dao(Person)
    await person_dao.add_person_identifiers(
        external_person.uid,
        [{"type": PersonIdentifierType.ORCID.value, "value": orcid_value}])
    external_before = await service.get_person(external_person.uid)
    assert _get_identifier(external_before, PersonIdentifierType.ORCID) is not None

    await service.add_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                 orcid_value, False, timestamp)

    internal_person = await service.get_person(person_uid)
    assert _get_identifier(internal_person, PersonIdentifierType.ORCID).value == orcid_value
    external_after = await service.get_person(external_person.uid)
    assert external_after is not None
    assert _get_identifier(external_after, PersonIdentifierType.ORCID) is None


async def test_confirm_identifier_authenticates(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with a non authenticated orcid
    When the orcid is confirmed through authentication (same value)
    Then the identifier is authenticated and validated, value unchanged
    """
    person_uid = "local-jdoe@univ-domain.edu"
    orcid_value = "0000-0001-2345-6789"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.confirm_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                     orcid_value, True, timestamp)

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier.value == orcid_value
    assert orcid_identifier.authenticated is True
    assert orcid_identifier.validated is True
    assert orcid_identifier.authentication_date == datetime.datetime.fromisoformat(
        timestamp.replace("Z", "+00:00"))


async def test_confirm_identifier_idempotent(
        persisted_person_a_orcid_hal_authenticated_pydantic_model: Person
        # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with an already authenticated orcid
    When the orcid is confirmed again with the same value (token refresh)
    Then the confirmation succeeds and refreshes the authentication date
    """
    person_uid = "local-jdoe_auth_orcid@univ-domain.edu"
    orcid_value = "0000-0001-2345-6789"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.confirm_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                     orcid_value, True, timestamp)

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier.value == orcid_value
    assert orcid_identifier.authenticated is True
    assert orcid_identifier.authentication_date == datetime.datetime.fromisoformat(
        timestamp.replace("Z", "+00:00"))


async def test_confirm_identifier_value_mismatch(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with an orcid identifier
    When a confirmation arrives with a different value
    Then the confirmation fails (value changes require remove + add) and nothing changes
    """
    person_uid = "local-jdoe@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    with pytest.raises(ValueError):
        await service.confirm_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                         "0000-0001-2345-4321", True, timestamp)

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier.value == "0000-0001-2345-6789"
    assert orcid_identifier.authenticated is False
    assert orcid_identifier.validated is False


async def test_confirm_identifier_missing(
        persisted_person_a_no_orcid_no_hal_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with no orcid identifier
    When a confirmation arrives for an orcid
    Then the confirmation fails (nothing to confirm)
    """
    person_uid = "local-jdoe_no_orcid@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    with pytest.raises(ValueError):
        await service.confirm_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                         "0000-0001-2345-6789", True, timestamp)


async def test_confirm_identifier_idref_never_authenticated(
        persisted_person_a_with_idref_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with a non validated idref
    When the idref is confirmed, even with the authenticated flag set
    Then the identifier is validated only (idref has no authentication process)
    """
    person_uid = "local-jdoe_with_idref@univ-domain.edu"
    timestamp = "2025-08-26T06:17:28.243Z"
    service = PeopleService()

    await service.confirm_identifier(person_uid, PersonIdentifierType.IDREF.value,
                                     "123456789", True, timestamp)

    person = await service.get_person(person_uid)
    idref_identifier = _get_identifier(person, PersonIdentifierType.IDREF)
    assert idref_identifier.validated is True
    assert idref_identifier.authenticated is False
    assert idref_identifier.authentication_date is None


async def test_remove_identifier(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with an orcid identifier
    When the orcid is removed
    Then the identifier is gone from the person and no person owns it anymore
    """
    person_uid = "local-jdoe@univ-domain.edu"
    orcid_value = "0000-0001-2345-6789"
    service = PeopleService()

    await service.remove_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                    orcid_value)

    person = await service.get_person(person_uid)
    assert _get_identifier(person, PersonIdentifierType.ORCID) is None
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao = factory.get_dao(Person)
    owner = await person_dao.find_by_identifier(PersonIdentifierType.ORCID, orcid_value)
    assert owner is None


async def test_remove_identifier_shared_node_preserved(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an internal person and an external person sharing the same AgentIdentifier
    When the identifier is removed from the internal person
    Then the AgentIdentifier node survives for the external owner
    """
    person_uid = "local-jdoe@univ-domain.edu"
    orcid_value = "0000-0001-2345-6789"
    service = PeopleService()

    external_person = Person(
        uid="scanr-test-external-shared",
        display_name="J. Doe",
        external=True,
        names=[],
        identifiers=[]
    )
    await service.create_person(external_person)
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    person_dao = factory.get_dao(Person)
    await person_dao.add_person_identifiers(
        external_person.uid,
        [{"type": PersonIdentifierType.ORCID.value, "value": orcid_value}])

    await service.remove_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                    orcid_value)

    internal_person = await service.get_person(person_uid)
    assert _get_identifier(internal_person, PersonIdentifierType.ORCID) is None
    external_after = await service.get_person(external_person.uid)
    assert _get_identifier(external_after, PersonIdentifierType.ORCID) is not None


async def test_remove_identifier_wrong_value(
        persisted_person_a_pydantic_model: Person  # pylint: disable=unused-argument
) -> None:
    """
    Given an existing person with an orcid identifier
    When a removal arrives with a different value
    Then the removal fails and the identifier is untouched
    """
    person_uid = "local-jdoe@univ-domain.edu"
    service = PeopleService()

    with pytest.raises(ValueError):
        await service.remove_identifier(person_uid, PersonIdentifierType.ORCID.value,
                                        "0000-0001-2345-4321")

    person = await service.get_person(person_uid)
    orcid_identifier = _get_identifier(person, PersonIdentifierType.ORCID)
    assert orcid_identifier is not None
    assert orcid_identifier.value == "0000-0001-2345-6789"



async def test_create_person_employment_resolved_by_identifier(
        person_a_json_data: dict,
        persisted_institution_a_pydantic_model: OrganizationBase,
) -> None:
    """
    Given a persisted institution with a local uid and a uai identifier
    When a person is created with an employment referencing the institution by uai
    Then the employment is attached to the existing institution
    and no duplicate institution is created from the registry
    """
    person_data = dict(person_a_json_data)
    person_data["memberships"] = []
    person_data["employments"] = [{"entity_uid": "uai-UAI001"}]
    person = Person(**person_data)
    service = PeopleService()
    await service.create_person(person)
    fetched_person = await service.get_person(person.uid)
    assert len(fetched_person.employments) == 1
    assert (fetched_person.employments[0].entity_uid
            == persisted_institution_a_pydantic_model.uid)
    assert await InstitutionService().institution_uid("uai-UAI001") is None
