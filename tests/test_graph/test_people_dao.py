from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person


async def test_create_person(basic_person_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    Then the person should be created in the database

    :param basic_person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(basic_person_pydantic_model)
    local_identifier = basic_person_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person = await dao.find_by_identifier(local_identifier.type,
                                          local_identifier.value)
    assert person
    assert person.id == f"{local_identifier.type.value}-{local_identifier.value}"
    assert any(
        name for name in person.names if
        any(
            literal for literal in name.first_names if literal.value == "John"
        ) and any(
            literal for literal in name.last_names if literal.value == "Doe"
        )
    )
    orcid_identifier = basic_person_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier for identifier in person.identifiers if
        identifier.type == orcid_identifier.type and identifier.value == orcid_identifier.value
    )


async def test_create_and_update_person_with_same_data(basic_person_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the update_person method is called with the same person
    Then the person should be created in the database
    and there should be only one instance of the person last name, fist name and identifier

    :param basic_person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(basic_person_pydantic_model)
    local_identifier = basic_person_pydantic_model.get_identifier(PersonIdentifierType.LOCAL)
    person = await dao.find_by_identifier(local_identifier.type,
                                          local_identifier.value)
    assert person
    await dao.update(basic_person_pydantic_model)
    person = await dao.find_by_identifier(local_identifier.type,
                                          local_identifier.value)
    assert person
    assert person.id == f"{local_identifier.type.value}-{local_identifier.value}"
    literal_last_names = await dao.find_literals_by_value_and_language("Doe", "fr")
    literal_first_names = await dao.find_literals_by_value_and_language("John", "fr")
    assert len(literal_last_names) == 1
    assert len(literal_first_names) == 1

async def test_create_and_get_person(basic_person_pydantic_model: Person):
    """
    Given a basic person Pydantic model
    When the create_person method is called
    And the get_person method is called with the person id
    Then the person should be created in the database
    and the person should be retrieved

    :param basic_person_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(basic_person_pydantic_model)
    person = await dao.get(basic_person_pydantic_model.id)
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
    orcid_identifier = basic_person_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier for identifier in retrieved_person.identifiers if
        identifier.type == orcid_identifier.type and identifier.value == orcid_identifier.value
    )
