from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure


async def test_create_research_structure(
        basic_research_structure_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    Then the research structure should be created in the database

    :param basic_research_structure_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(basic_research_structure_pydantic_model)
    local_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.id == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    rnsr_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_structure.names) == 2
    literal_fr = basic_research_structure_pydantic_model.get_name("fr")
    assert any(
        name for name in research_structure.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = basic_research_structure_pydantic_model.get_name("en")
    assert any(
        name for name in research_structure.names if
        name.language == literal_en.language and name.value == literal_en.value
    )


async def test_create_and_update_research_structure_with_same_data(
        basic_research_structure_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    And the update_research_structure method is called with the same data
    Then the research structure should be unchanged in the database
    :param basic_research_structure_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(basic_research_structure_pydantic_model)
    local_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    await dao.update(basic_research_structure_pydantic_model)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.id == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    rnsr_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = basic_research_structure_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_structure.names) == 2
    literal_fr = basic_research_structure_pydantic_model.get_name("fr")
    assert any(
        name for name in research_structure.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = basic_research_structure_pydantic_model.get_name("en")
    assert any(
        name for name in research_structure.names if
        name.language == literal_en.language and name.value == literal_en.value
    )
