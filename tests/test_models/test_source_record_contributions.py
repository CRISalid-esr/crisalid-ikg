from app.models.loc_contribution_role import LocContributionRole
from app.models.source_organizations import SourceOrganization
from app.models.source_records import SourceRecord

def test_hal_chapter_source_record(
        hal_chapter_a_source_record_json_data: dict
):
    """
    Given a source record model recording a chapter harvested from HAL
    with detailed contributor information
    When asked for different field values
    Then the values should be returned correctly
    :param scanr_thesis_source_record_json_data:
    :return:
    """
    source_record = SourceRecord(**hal_chapter_a_source_record_json_data)
    assert source_record
    contribution_0 = next(
        (c for c in source_record.contributions if c.rank == 0),
        None
    )
    assert contribution_0
    assert contribution_0.role == LocContributionRole.AUTHOR
    assert contribution_0.contributor.name == 'Alice Dupont'
    organisation_0 = contribution_0.affiliations[0]
    assert organisation_0.source == 'hal'
    assert organisation_0.source_identifier == '2001'
    assert organisation_0.name == 'Université Anonyme'
    assert organisation_0.type == SourceOrganization.SourceOrganisationType.INSTITUTION
    assert len(organisation_0.identifiers) == 4
    assert any(
        i.type == 'hal' and i.value == '2001'
        for i in organisation_0.identifiers
    )
    assert any(
        i.type == 'idref' and i.value == '123456789'
        for i in organisation_0.identifiers
    )
    assert any(
        i.type == 'isni' and i.value == '000000012345678X'
        for i in organisation_0.identifiers
    )
    assert any(
        i.type == 'ror' and i.value == 'https://ror.org/000000000'
        for i in organisation_0.identifiers
    )
