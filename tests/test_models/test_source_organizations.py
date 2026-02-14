from app.models.harvesting_sources import HarvestingSource
from app.models.source_organizations import SourceOrganization


def test_create_valid_source_institution(hal_source_institution_json_data):
    """
    Given json data for a source organization of type institution
    When loaded into the Pydantic model
    Then the model should be created correctly
    :param hal_source_institution_json_data:
    :return:
    """
    source_institution = SourceOrganization(**hal_source_institution_json_data)
    assert source_institution
    assert source_institution.source == HarvestingSource.HAL
    assert source_institution.source_identifier == '2001'
    assert source_institution.name == 'Université Anonyme'
    assert source_institution.type == SourceOrganization.SourceOrganisationType.INSTITUTION
    assert len(source_institution.identifiers) == 4
    assert any(
        i.type == 'hal' and i.value == '2001'
        for i in source_institution.identifiers
    )
    assert any(
        i.type == 'idref' and i.value == '123456789'
        for i in source_institution.identifiers
    )
    assert any(
        i.type == 'isni' and i.value == '000000012345678X'
        for i in source_institution.identifiers
    )
    assert any(
        i.type == 'ror' and i.value == 'https://ror.org/000000000'
        for i in source_institution.identifiers
    )


def test_create_valid_source_laboratory(hal_source_laboratory_json_data):
    """
    Given json data for a source organization of type laboratory
    When loaded into the Pydantic model
    Then the model should be created correctly
    :param hal_source_laboratory_json_data:
    :return:
    """
    source_laboratory = SourceOrganization(**hal_source_laboratory_json_data)
    assert source_laboratory
    assert source_laboratory.source == HarvestingSource.HAL
    assert source_laboratory.source_identifier == '3002'
    assert source_laboratory.name == 'Laboratoire Interdisciplinaire'
    assert source_laboratory.type == SourceOrganization.SourceOrganisationType.LABORATORY
    assert len(source_laboratory.identifiers) == 2
    assert any(
        i.type == 'hal' and i.value == '3002'
        for i in source_laboratory.identifiers
    )
    assert any(
        i.type == 'ror' and i.value == 'https://ror.org/000000001'
        for i in source_laboratory.identifiers
    )
