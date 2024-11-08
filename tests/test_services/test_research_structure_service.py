from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure
from app.services.organizations.research_structure_service import ResearchStructureService


async def test_create_structure(
        research_structure_a_pydantic_model: ResearchStructure
) -> None:
    """
    Given a basic research structure pydantic model
    When the structure is added to the graph
    Then the structure can be read from the graph
    """
    service = ResearchStructureService()
    await service.create_structure(research_structure_a_pydantic_model)
    identifier_value = next(identifier.value for identifier in
                        research_structure_a_pydantic_model.identifiers if identifier.type ==
                        OrganizationIdentifierType.LOCAL)
    fetched_structure = await service.get_structure(identifier_value)
    assert fetched_structure
    assert len(fetched_structure.descriptions) == len(
        research_structure_a_pydantic_model.descriptions)
    assert all(
        description in fetched_structure.descriptions
        for description in research_structure_a_pydantic_model.descriptions
    )
    assert fetched_structure.acronym == research_structure_a_pydantic_model.acronym
