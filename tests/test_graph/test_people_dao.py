from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.models.research_structures import ResearchStructure


async def test_create_person(person_pydantic_model: Person,
                             persisted_research_structure_pydantic_model: ResearchStructure):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_pydantic_model)
    local_identifier = person_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person_from_db = await dao.find_by_identifier(local_identifier.type,
                                                  local_identifier.value)
    assert person_from_db
    assert person_from_db.id == f"{local_identifier.type.value}-{local_identifier.value}"
    assert any(
        name for name in person_from_db.names if
        any(
            literal for literal in name.first_names if literal.value == "John"
        ) and any(
            literal for literal in name.last_names if literal.value == "Doe"
        )
    )
    orcid_identifier = person_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier for identifier in person_from_db.identifiers if
        identifier.type == orcid_identifier.type and identifier.value == orcid_identifier.value
    )
    assert person_from_db.memberships
    assert any(
        membership for membership in person_from_db.memberships if
        membership.entity_id == persisted_research_structure_pydantic_model.id
    )


async def test_create_and_update_person_with_same_data(person_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the update_person method is called with the same person
    Then the person should be created in the database
    and there should be only one instance of the person last name, fist name and identifier

    :param person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_pydantic_model)
    local_identifier = person_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person = await dao.find_by_identifier(local_identifier.type,
                                          local_identifier.value)
    assert person
    await dao.update(person_pydantic_model)
    person = await dao.find_by_identifier(local_identifier.type,
                                          local_identifier.value)
    assert person
    assert person.id == f"{local_identifier.type.value}-{local_identifier.value}"
    literal_last_names = await dao.find_literals_by_value_and_language("Doe", "fr")
    literal_first_names = await dao.find_literals_by_value_and_language("John", "fr")
    assert len(literal_last_names) == 1
    assert len(literal_first_names) == 1


async def test_create_and_get_person(person_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the get_person method is called with the person id
    Then the person should be created in the database
    and the person should be retrieved

    :param person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_pydantic_model)
    person = await dao.get(person_pydantic_model.id)
    assert person
    retrieved_person = await dao.get(person.id)
    assert retrieved_person
    assert retrieved_person.id == person.id
    assert any(
        name for name in retrieved_person.names if
        any(
            literal for literal in name.first_names if literal.value == "John"
        ) and any(
            literal for literal in name.last_names if literal.value == "Doe"
        )
    )
    orcid_identifier = person_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier for identifier in retrieved_person.identifiers if
        identifier.type == orcid_identifier.type and identifier.value == orcid_identifier.value
    )


async def test_create_person_with_two_names(person_with_two_names_pydantic_model: Person):
    """
    Given a basic person Pydantic model with two names
    When the create_person method is called
    Then the person should be created in the database

    :param person_with_two_names_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_with_two_names_pydantic_model)
    local_identifier = person_with_two_names_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL)
    person_from_db = await dao.find_by_identifier(local_identifier.type,
                                                  local_identifier.value)
    assert person_from_db
    assert person_from_db.id == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(person_from_db.names) == 2
    assert any(
        name for name in person_from_db.names if
        any(
            literal for literal in name.first_names if literal.value == "Jeanne"
        ) and any(
            literal for literal in name.last_names if literal.value == "Dupont"
        )
    )
    assert any(
        name for name in person_from_db.names if
        any(
            literal for literal in name.first_names if literal.value == "Jeanne"
        ) and any(
            literal for literal in name.last_names if literal.value == "Durand"
        )
    )


async def test_create_person_with_names_in_multiple_lng(
    person_with_name_in_multiple_lng_pydantic_model:Person):
    """
    Given a person Pydantic model with names in multiple languages
    When the create_person method is called
    Then the person should be created in the database
    :param person_with_name_in_multiple_lng_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person_with_name_in_multiple_lng_pydantic_model)
    local_identifier = person_with_name_in_multiple_lng_pydantic_model.get_identifier(
        PersonIdentifierType.LOCAL)
    person_from_db = await dao.find_by_identifier(local_identifier.type,
                                                  local_identifier.value)
    assert person_from_db
    assert person_from_db.id == f"{local_identifier.type.value}-{local_identifier.value}"
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
