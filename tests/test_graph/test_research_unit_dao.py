from collections import Counter

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.research_unit_dao import ResearchUnitDAO
from app.models.agent_identifiers import AgentIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_units import ResearchUnit


async def test_create_research_unit(
        test_app,  # pylint: disable=unused-argument
        research_unit_a_pydantic_model: ResearchUnit):
    """
    Given a basic research structure Pydantic model
    When the create_research_unit method is called
    Then the research structure should be created in the database

    :param research_unit_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    await dao.create(research_unit_a_pydantic_model)
    local_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_unit = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_unit
    assert research_unit.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_unit.identifiers) == 3
    rnsr_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_unit.names) == 2
    literal_fr = research_unit_a_pydantic_model.get_name("fr")
    assert any(
        name for name in research_unit.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = research_unit_a_pydantic_model.get_name("en")
    assert any(
        name for name in research_unit.names if
        name.language == literal_en.language and name.value == literal_en.value
    )


async def test_create_and_update_research_unit_with_same_data(
        research_unit_a_pydantic_model: ResearchUnit):
    """
    Given a basic research structure Pydantic model
    When the create_research_unit method is called
    And the update_research_unit method is called with the same data
    Then the research structure should be unchanged in the database
    :param research_unit_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    await dao.create(research_unit_a_pydantic_model)
    local_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_unit = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_unit
    await dao.update(research_unit_a_pydantic_model)
    research_unit = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_unit
    assert research_unit.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_unit.identifiers) == 3
    rnsr_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )
    ror_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    assert len(research_unit.names) == 2
    literal_fr = research_unit_a_pydantic_model.get_name("fr")
    assert any(
        name for name in research_unit.names if
        name.language == literal_fr.language and name.value == literal_fr.value
    )
    literal_en = research_unit_a_pydantic_model.get_name("en")
    assert any(
        name for name in research_unit.names if
        name.language == literal_en.language and name.value == literal_en.value
    )


async def test_switch_research_unit_identifier(
        research_unit_a_pydantic_model: ResearchUnit):
    """
    Given a basic research structure Pydantic model
    When the create_research_unit method is called
    And the update_research_unit method is called with a different identifier
    Then the research structure should be updated in the database

    :param research_unit_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    await dao.create(research_unit_a_pydantic_model)
    local_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_unit = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_unit
    # Remove the RNSR identifier and add an IdRef identifier
    research_unit_a_pydantic_model.identifiers = [
        identifier for identifier in research_unit_a_pydantic_model.identifiers
        if identifier.type != OrganizationIdentifierType.RNSR
    ]
    research_unit_a_pydantic_model.identifiers.append(
        AgentIdentifier(type=OrganizationIdentifierType.IDREF, value="123456789")
    )
    await dao.update(research_unit_a_pydantic_model)
    research_unit = await dao.find_by_identifier(OrganizationIdentifierType.LOCAL,
                                                      local_identifier.value)
    assert research_unit
    assert research_unit.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_unit.identifiers) == 3
    ror_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    idref_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.IDREF)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == idref_identifier.type and identifier.value == idref_identifier.value
    )


async def test_update_research_unit_rnsr_identifier(
        research_unit_a_pydantic_model: ResearchUnit):
    """
    Given a basic research structure Pydantic model
    When the create_research_unit method is called
    And the update_research_unit method is called with a different RNSR identifier
    Then the research structure should be updated in the database
    :param research_unit_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    await dao.create(research_unit_a_pydantic_model)
    local_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL)
    research_unit = await dao.find_by_identifier(local_identifier.type,
                                                      local_identifier.value)
    assert research_unit
    # Remove the RNSR identifier and add a new one
    research_unit_a_pydantic_model.identifiers = [
        identifier for identifier in research_unit_a_pydantic_model.identifiers
        if identifier.type != OrganizationIdentifierType.RNSR
    ]
    research_unit_a_pydantic_model.identifiers.append(
        AgentIdentifier(type=OrganizationIdentifierType.RNSR, value="123456789")
    )
    await dao.update(research_unit_a_pydantic_model)
    research_unit = await dao.find_by_identifier(OrganizationIdentifierType.LOCAL,
                                                      local_identifier.value)
    assert research_unit
    assert research_unit.uid == f"{local_identifier.type.value}-{local_identifier.value}"
    assert len(research_unit.identifiers) == 3
    ror_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.ROR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == ror_identifier.type and identifier.value == ror_identifier.value
    )
    rnsr_identifier = research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.RNSR)
    assert any(
        identifier for identifier in research_unit.identifiers if
        identifier.type == rnsr_identifier.type and identifier.value == rnsr_identifier.value
    )


async def test_update_research_unit_name(
        persisted_research_unit_a_pydantic_model: ResearchUnit,
        research_unit_a_with_updated_name_pydantic_model: ResearchUnit,
):
    """
    Given a basic research structure Pydantic model
    When the create_research_unit method is called
    And the update_research_unit method is called with a different name
    Then the research structure should be updated in the database
    :param research_unit_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    local_identifier = persisted_research_unit_a_pydantic_model.get_identifier(
        OrganizationIdentifierType.LOCAL
    )
    research_unit = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert research_unit
    assert research_unit.uid == "local-U123"
    assert len(research_unit.names) == len(
        persisted_research_unit_a_pydantic_model.names
    )
    structure_names = Counter(
        (literal.value, literal.language) for literal in research_unit.names
    )
    persist_structure_names = Counter(
        (literal.value, literal.language)
        for literal in persisted_research_unit_a_pydantic_model.names
    )
    assert structure_names == persist_structure_names

    await dao.update(research_unit_a_with_updated_name_pydantic_model)
    updated_research_unit = await dao.find_by_identifier(
        local_identifier.type, local_identifier.value
    )
    assert updated_research_unit.uid == research_unit.uid
    updated_structure_names = Counter(
        (literal.value, literal.language)
        for literal in updated_research_unit.names
    )
    updated_pydantic_structure_names = Counter(
        (literal.value, literal.language)
        for literal in research_unit_a_with_updated_name_pydantic_model.names
    )
    assert structure_names != updated_structure_names
    assert updated_structure_names == updated_pydantic_structure_names


async def test_get_research_unit_by_uid(
        persisted_research_unit_a_pydantic_model: ResearchUnit):
    """
    Given a persisted research structure Pydantic model
    When the get_research_unit_by_uid method is called
    Then the research structure should be retrieved from the database
    :param persisted_research_unit_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao:ResearchUnitDAO = factory.get_dao(ResearchUnit)
    research_unit = await dao.get(persisted_research_unit_a_pydantic_model.uid)
    assert research_unit
    assert research_unit.uid == persisted_research_unit_a_pydantic_model.uid
    assert len(research_unit.names) == len(persisted_research_unit_a_pydantic_model.names)
    structure_names = Counter(
        (literal.value, literal.language) for literal in research_unit.names
    )
    persist_structure_names = Counter(
        (literal.value, literal.language)
        for literal in persisted_research_unit_a_pydantic_model.names
    )
    assert structure_names == persist_structure_names
    assert len(research_unit.identifiers) == len(
        persisted_research_unit_a_pydantic_model.identifiers
    )
    structure_identifiers = Counter(
        (identifier.type.value, identifier.value) for identifier in research_unit.identifiers
    )
    persist_structure_identifiers = Counter(
        (identifier.type.value, identifier.value)
        for identifier in persisted_research_unit_a_pydantic_model.identifiers
    )
    assert structure_identifiers == persist_structure_identifiers
