from unittest.mock import patch, AsyncMock

import pytest

from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure
from app.services.organizations.research_structure_service import ResearchStructureService


@pytest.fixture(name="mocked_structure_created_signal")
def mocked_structure_created_signal_fixture():
    """
    Fixture to mock the `structure_created` signal.
    """
    with patch("app.signals.structure_created.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


async def test_create_structure(
        test_app,  # pylint: disable=unused-argument
        research_structure_a_pydantic_model: ResearchStructure,
        mocked_structure_created_signal  # Use the mocked signal fixture
) -> None:
    """
    Given a basic research structure Pydantic model
    When the structure is added to the graph
    Then the structure can be read from the graph and signal is called
    """
    service = ResearchStructureService()
    await service.create_structure(research_structure_a_pydantic_model)

    identifier_value = next(
        identifier.value for identifier in research_structure_a_pydantic_model.identifiers
        if identifier.type == OrganizationIdentifierType.LOCAL
    )

    fetched_structure = await service.get_structure_by_identifier(identifier_value)
    assert fetched_structure
    assert len(fetched_structure.descriptions) == len(
        research_structure_a_pydantic_model.descriptions)
    assert all(
        description in fetched_structure.descriptions
        for description in research_structure_a_pydantic_model.descriptions
    )
    assert fetched_structure.acronym == research_structure_a_pydantic_model.acronym

    # Assert that the signal was called with the correct parameters
    mocked_structure_created_signal.assert_called_once_with(
        service, payload=research_structure_a_pydantic_model.uid
    )
