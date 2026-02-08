from app.models.harvesting_sources import HarvestingSource
from app.models.source_organizations import SourceOrganization
from app.services.source_contributors.source_organization_service import SourceOrganizationService


async def test_create_source_institution(hal_source_institution_pydantic_model: SourceOrganization
                                         ) -> None:
    """
    Given a source organization Pydantic model
    When the source record is added to the graph
    Then the source record can be read from the graph
    :param hal_source_institution_pydantic_model:
    :return:
    """
    service = SourceOrganizationService()
    await service.create_or_update_source_organization(
        source_organization=hal_source_institution_pydantic_model)
    source_institution = await service.get_source_organization_by_uid(
        hal_source_institution_pydantic_model.uid)
    assert source_institution
    assert source_institution.identifiers
    assert len(source_institution.identifiers) == 4
    assert any(
        identifier.type == 'hal' and identifier.value == '2001' for
        identifier in
        source_institution.identifiers)
    assert any(
        identifier.type == 'idref' and identifier.value == '123456789' for
        identifier in
        source_institution.identifiers)
    assert any(
        identifier.type == 'isni' and identifier.value == '000000012345678X' for
        identifier in
        source_institution.identifiers)
    assert any(
        identifier.type == 'ror' and identifier.value == 'https://ror.org/000000000' for
        identifier in
        source_institution.identifiers)
    assert source_institution.source == HarvestingSource.HAL
    assert source_institution.source_identifier == '2001'
    assert source_institution.name == 'Université Anonyme'
    assert source_institution.type == SourceOrganization.SourceOrganisationType.INSTITUTION


async def test_create_source_laboratory(hal_source_laboratory_pydantic_model: SourceOrganization
                                        ) -> None:
    """
    Given a source organization Pydantic model
    When the source record is added to the graph
    Then the source record can be read from the graph
    :param hal_source_laboratory_pydantic_model:
    :return:
    """
    service = SourceOrganizationService()
    await service.create_or_update_source_organization(
        source_organization=hal_source_laboratory_pydantic_model)
    source_laboratory = await service.get_source_organization_by_uid(
        hal_source_laboratory_pydantic_model.uid)
    assert source_laboratory
    assert source_laboratory.identifiers
    assert len(source_laboratory.identifiers) == 2
    assert any(
        identifier.type == 'hal' and identifier.value == '3002' for
        identifier in
        source_laboratory.identifiers)
    assert any(
        identifier.type == 'ror' and identifier.value == 'https://ror.org/000000001' for
        identifier in
        source_laboratory.identifiers)
    assert source_laboratory.source == HarvestingSource.HAL
    assert source_laboratory.source_identifier == '3002'
    assert source_laboratory.name == 'Laboratoire Interdisciplinaire'
    assert source_laboratory.type == SourceOrganization.SourceOrganisationType.LABORATORY


async def test_create_source_org_without_type(
        hal_source_org_without_type_pydantic_model: SourceOrganization
) -> None:
    """
    Given a source organization Pydantic model without type
    When the source record is added to the graph
    Then the source record can be read from the graph with type set to ORGANIZATION
    :param hal_source_org_without_type_pydantic_model:
    :return:
    """
    service = SourceOrganizationService()
    await service.create_or_update_source_organization(
        source_organization=hal_source_org_without_type_pydantic_model)
    source_org = await service.get_source_organization_by_uid(
        hal_source_org_without_type_pydantic_model.uid)
    assert source_org
    assert source_org.identifiers
    assert len(source_org.identifiers) == 1
    assert source_org.identifiers[0].type == 'hal'
    assert source_org.identifiers[0].value == '9999'
    assert source_org.name == 'Organization Without Type'
    assert source_org.type is SourceOrganization.SourceOrganisationType.ORGANIZATION
