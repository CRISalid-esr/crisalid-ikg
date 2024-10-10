from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.agent_identifiers import AgentIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure


async def test_create_research_structure(
        research_structure_a_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    Then the research structure should be created in the database

    :param research_structure_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_a_pydantic_model)
    local_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    rnsr_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_structure.names) == 2
    literal_fr = research_structure_a_pydantic_model.get_name("fr")
    assert any(
        name for name in research_structure.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = research_structure_a_pydantic_model.get_name("en")
    assert any(
        name for name in research_structure.names if
        name.language == literal_en.language and name.value == literal_en.value
    )


async def test_create_and_update_research_structure_with_same_data(
        research_structure_a_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    And the update_research_structure method is called with the same data
    Then the research structure should be unchanged in the database
    :param research_structure_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_a_pydantic_model)
    local_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    await dao.update(research_structure_a_pydantic_model)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    rnsr_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_structure.names) == 2
    literal_fr = research_structure_a_pydantic_model.get_name("fr")
    assert any(
        name for name in research_structure.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = research_structure_a_pydantic_model.get_name("en")
    assert any(
        name for name in research_structure.names if
        name.language == literal_en.language and name.value == literal_en.value
    )


async def test_switch_research_structure_identifier(
        research_structure_a_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    And the update_research_structure method is called with a different identifier
    Then the research structure should be updated in the database

    :param research_structure_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_a_pydantic_model)
    local_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    # Remove the RNSR identifier and add an IdRef identifier
    research_structure_a_pydantic_model.identifiers = [
        identifier for identifier in research_structure_a_pydantic_model.identifiers
        if identifier.type != OrganizationIdentifierType.RNSR
    ]
    research_structure_a_pydantic_model.identifiers.append(
        AgentIdentifier(type=OrganizationIdentifierType.IDREF, value="123456789")
    )
    await dao.update(research_structure_a_pydantic_model)
    research_structure = await dao.find_by_identifier(OrganizationIdentifierType.LOCAL,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    ror_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    idref_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.IDREF)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == idref_identifier.type and identifier.value == idref_identifier.value
    )


async def test_update_research_structure_rnsr_identifier(
        research_structure_a_pydantic_model: ResearchStructure):
    """
    Given a basic research structure Pydantic model
    When the create_research_structure method is called
    And the update_research_structure method is called with a different RNSR identifier
    Then the research structure should be updated in the database
    :param research_structure_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(ResearchStructure)
    await dao.create(research_structure_a_pydantic_model)
    local_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_structure = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_structure
    # Remove the RNSR identifier and add a new one
    research_structure_a_pydantic_model.identifiers = [
        identifier for identifier in research_structure_a_pydantic_model.identifiers
        if identifier.type != OrganizationIdentifierType.RNSR
    ]
    research_structure_a_pydantic_model.identifiers.append(
        AgentIdentifier(type=OrganizationIdentifierType.RNSR, value="123456789")
    )
    await dao.update(research_structure_a_pydantic_model)
    research_structure = await dao.find_by_identifier(OrganizationIdentifierType.LOCAL,
                                                      local_identifier.value)
    assert research_structure
    assert research_structure.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_structure.identifiers) == 3
    ror_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    rnsr_identifier = research_structure_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_structure.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
   