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
        "John" in name.first_names and "Doe" in name.family_names and "Johnny" in name.other_names
    )
    orcid_identifier = basic_person_pydantic_model.get_identifier(PersonIdentifierType.ORCID)
    assert any(
        identifier for identifier in person.identifiers if
        identifier.type == orcid_identifier.type and identifier.value == orcid_identifier.value
    )
