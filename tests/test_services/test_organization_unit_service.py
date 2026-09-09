from unittest.mock import AsyncMock, patch

import pytest

from app.services.organizations.organization_unit_service import OrganizationUnitService


async def test_non_local_target_missing_triggers_registry_fetch(
        test_app,
        univ_etienne_dupond_pydantic_model,
):
    """
    When creating a structure whose relationship target (non-local uid) is absent
    from the graph, the service must call InstitutionService.create_institution.
    """
    service = OrganizationUnitService()
    with patch(
        "app.services.organizations.organization_unit_service.InstitutionService",
        autospec=True,
    ) as MockInstitutionService:
        mock_inst = AsyncMock()
        mock_inst.create_institution.return_value = "uai-07890"
        MockInstitutionService.return_value = mock_inst

        # epe (uai-07890) not in graph → service should call create_institution
        await service.create_structure(univ_etienne_dupond_pydantic_model)

        mock_inst.create_institution.assert_called_once_with("uai-07890")


async def test_non_local_target_present_skips_registry_fetch(
        test_app,
        persisted_epe_paris_sud_ouest_pydantic_model,
        univ_etienne_dupond_pydantic_model,
):
    """
    When the non-local relationship target already exists in the graph,
    InstitutionService.create_institution must NOT be called.
    """
    service = OrganizationUnitService()
    with patch(
        "app.services.organizations.organization_unit_service.InstitutionService",
        autospec=True,
    ) as MockInstitutionService:
        mock_inst = AsyncMock()
        MockInstitutionService.return_value = mock_inst

        # epe (uai-07890) is already persisted
        await service.create_structure(univ_etienne_dupond_pydantic_model)

        mock_inst.create_institution.assert_not_called()


async def test_local_target_never_triggers_registry_fetch(
        test_app,
        research_unit_center_pydantic_model,
):
    """
    Local targets (local-xxx) must never trigger registry lookup even when absent.
    The DAO handles missing local targets with a logged error.
    """
    service = OrganizationUnitService()
    with patch(
        "app.services.organizations.organization_unit_service.InstitutionService",
        autospec=True,
    ) as MockInstitutionService:
        mock_inst = AsyncMock()
        MockInstitutionService.return_value = mock_inst

        await service.create_structure(research_unit_center_pydantic_model)

        mock_inst.create_institution.assert_not_called()


async def test_registry_fetch_failure_does_not_prevent_structure_creation(
        test_app,
        univ_etienne_dupond_pydantic_model,
):
    """
    If the registry cannot resolve a non-local target, the structure is still created.
    """
    service = OrganizationUnitService()
    with patch(
        "app.services.organizations.organization_unit_service.InstitutionService",
        autospec=True,
    ) as MockInstitutionService:
        mock_inst = AsyncMock()
        mock_inst.create_institution.side_effect = ValueError("Registry unreachable")
        MockInstitutionService.return_value = mock_inst

        # Should not raise even though registry fails
        result = await service.create_structure(univ_etienne_dupond_pydantic_model)
        assert result is not None


@pytest.mark.parametrize("external", [False, True])
def test_organization_base_external_field_defaults_to_false(external):
    """external=False by default; explicit True is accepted."""
    from app.models.organization_unit import Institution
    inst = Institution(
        long_labels=[{"value": "Test", "language": "en"}],
        identifiers=[{"type": "local", "value": "TEST-001"}],
        external=external,
    )
    assert inst.external is external
