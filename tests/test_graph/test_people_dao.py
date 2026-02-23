from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.models.research_structures import ResearchStructure


async def test_create_person(
        person_a_pydantic_model: Person,
        persisted_research_structure_a_pydantic_model: ResearchStructure,
):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param person_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_a_pydantic_model)
    local_identifier = person_a_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert (
            person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    )
    assert any(
        name
        for name in person_from_db.names
        if any(literal for literal in name.first_names if literal.value == "John")
        and any(literal for literal in name.last_names if literal.value == "Doe")
    )
    orcid_identifier = person_a_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier
        for identifier in person_from_db.identifiers
        if identifier.type == orcid_identifier.type
        and identifier.value == orcid_identifier.value
    )
    assert person_from_db.memberships
    assert any(
        membership
        for membership in person_from_db.memberships
        if membership.entity_uid == persisted_research_structure_a_pydantic_model.uid
    )


async def test_create_and_update_person_with_same_data(person_a_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the update_person method is called with the same person
    Then the person should be created in the database
    and there should be only one instance of the person last name, fist name and identifier

    :param person_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_a_pydantic_model)
    local_identifier = person_a_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person = await dao.find_by_identifier(local_identifier.type, local_identifier.value)
    assert person
    await dao.update(person_a_pydantic_model)
    person = await dao.find_by_identifier(local_identifier.type, local_identifier.value)
    assert person
    assert person.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    literal_last_names = await dao.find_literals_by_value_and_language("Doe", "fr")
    literal_first_names = await dao.find_literals_by_value_and_language("John", "fr")
    assert len(literal_last_names) == 1
    assert len(literal_first_names) == 1


async def test_create_and_get_person(person_a_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the get_person method is called with the person uid
    Then the person should be created in the database
    and the person should be retrieved

    :param person_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_a_pydantic_model)
    person = await dao.get(person_a_pydantic_model.uid)
    assert person
    retrieved_person = await dao.get(person.uid)
    assert retrieved_person
    assert retrieved_person.uid == person.uid
    assert any(
        name
        for name in retrieved_person.names
        if any(literal for literal in name.first_names if literal.value == "John")
        and any(literal for literal in name.last_names if literal.value == "Doe")
    )
    orcid_identifier = person_a_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier
        for identifier in retrieved_person.identifiers
        if identifier.type == orcid_identifier.type
        and identifier.value == orcid_identifier.value
    )


async def test_create_person_b_with_two_names(
        person_b_with_two_names_pydantic_model: Person,
):
    """
    Given a basic person Pydantic model with two names
    When the create_person method is called
    Then the person should be created in the database

    :param person_b_with_two_names_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_b_with_two_names_pydantic_model)
    local_identifier = person_b_with_two_names_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert (
            person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    )
    assert len(person_from_db.names) == 2
    assert any(
        name
        for name in person_from_db.names
        if any(literal for literal in name.first_names if literal.value == "Jeanne")
        and any(literal for literal in name.last_names if literal.value == "Dupont")
    )
    assert any(
        name
        for name in person_from_db.names
        if any(literal for literal in name.first_names if literal.value == "Jeanne")
        and any(literal for literal in name.last_names if literal.value == "Durand")
    )


async def test_create_person_c_with_two_last_names(
        person_c_with_two_last_names_pydantic_model: Person,
):
    """
    Given a person Pydantic model with two last names
    When the create_person method is called
    Then the person should be created in the database

    :param person_b_with_two_names_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_c_with_two_last_names_pydantic_model)
    local_identifier = person_c_with_two_last_names_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert (
            person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    )
    assert len(person_from_db.names) == 1
    assert len(person_from_db.names[0].last_names) == 2
    assert len(person_from_db.names[0].first_names) == 1
    assert any(
        name
        for name in person_from_db.names
        if any(literal for literal in name.first_names if literal.value == "Jane")
        and any(literal for literal in name.last_names if literal.value == "Done")
        and any(literal for literal in name.last_names if literal.value == "Mariée")
    )
    assert len(person_from_db.identifiers) == 2
    assert any(
        identifier.type == PersonIdentifierType.ORCID
        and identifier.value == "0000-0001-2345-6789"
        for identifier in person_from_db.identifiers
    ) and any(
        identifier.type == PersonIdentifierType.LOCAL
        and identifier.value == "jdone@univ-domain.edu"
        for identifier in person_from_db.identifiers
    )


async def test_create_person_with_names_in_multiple_lng(
        person_a_with_name_in_multiple_lng_pydantic_model: Person):
    """
    Given a person Pydantic model with names in multiple languages
    When the create_person method is called
    Then the person should be created in the database
    :param person_a_with_name_in_multiple_lng_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_a_with_name_in_multiple_lng_pydantic_model)
    local_identifier = person_a_with_name_in_multiple_lng_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL)
    person_from_db = await dao.find_by_identifier(local_identifier.type,
                                                  local_identifier.value)
    assert person_from_db
    assert person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(person_from_db.names) == 1
    assert any(
        name for name in person_from_db.names if
        any(
            literal for literal in name.first_names if
            literal.value == "John" and literal.language == "fr"
        ) and any(
            literal for literal in name.first_names if
            literal.value == "Михаил Александрович" and literal.language == "ru"
        ) and any(
            literal for literal in name.last_names if
            literal.value == "Doe" and literal.language == "fr"
        ) and any(
            literal for literal in name.last_names if
            literal.value == "Бакунин" and literal.language == "ru"
        )
    )


async def test_create_person_with_mononym(
        person_with_mononym_pydantic_model: Person,
):
    """
    Given a person Pydantic model with a mononym
    When the create_person method is called
    Then the person should be created in the database

    :param person_with_mononym_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_with_mononym_pydantic_model)
    local_identifier = person_with_mononym_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert (
            person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    )
    assert len(person_from_db.names) == 1
    assert len(person_from_db.names[0].first_names) == 1
    assert len(person_from_db.names[0].last_names) == 0
    assert any(
        name
        for name in person_from_db.names
        if any(literal for literal in name.first_names if literal.value == "Jeanne")
    )


async def test_create_person_d_with_two_memberships(
        person_d_with_two_memberships_pydantic_model: Person,
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        persisted_research_structure_b_pydantic_model: ResearchStructure,  #
):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param person_d_with_two_memberships_pydantic_model:
    :param persisted_research_structure_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_d_with_two_memberships_pydantic_model)
    local_identifier = person_d_with_two_memberships_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert (
            person_from_db.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    )
    assert len(person_d_with_two_memberships_pydantic_model.memberships) == 2
    assert len(person_from_db.memberships) == len(
        person_d_with_two_memberships_pydantic_model.memberships
    )

    assert all(
        uid in {membership.entity_uid for membership in person_from_db.memberships}
        for uid in {
            membership.entity_uid
            for membership in person_d_with_two_memberships_pydantic_model.memberships
        }
    )

    assert all(
        uid in {membership.entity_uid for membership in person_from_db.memberships}
        for uid in [
            persisted_research_structure_a_pydantic_model.uid,
            persisted_research_structure_b_pydantic_model.uid,
        ]
    )


async def test_update_existing_person_membership(
        persisted_research_structure_a_pydantic_model: ResearchStructure,
        persisted_research_structure_b_pydantic_model: ResearchStructure,
        persisted_person_a_pydantic_model: Person,
        person_a_with_different_membership_pydantic_model: Person,
):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param person_d_with_two_memberships_pydantic_model:
    :param persisted_research_structure_a_pydantic_model:
    :return:
    """
    # pylint: disable=duplicate-code
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    local_identifier = persisted_person_a_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL
    )
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert len(person_from_db.memberships) == 1
    assert any(
        membership
        for membership in person_from_db.memberships
        if membership.entity_uid == persisted_research_structure_a_pydantic_model.uid

    )
    await dao.update(person_a_with_different_membership_pydantic_model)
    person_from_db = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert person_from_db
    assert len(person_from_db.memberships) == 1
    assert any(
        membership
        for membership in person_from_db.memberships
        if
        membership.entity_uid == persisted_research_structure_b_pydantic_model.uid

    )
