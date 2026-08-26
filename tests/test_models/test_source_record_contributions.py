from app.models.harvesting_sources import HarvestingSource
from app.models.loc_contribution_role import LocContributionRole
from app.models.source_contributions import SourceContribution
from app.models.source_organizations import SourceOrganization
from app.models.source_people import SourcePerson
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
    assert organisation_0.source == HarvestingSource.HAL
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


def _minimal_contributor() -> dict:
    return {
        "source": "idref",
        "source_identifier": "123456789",
        "name": "Alice Dupont",
    }


def test_contribution_without_role_defaults_to_contributor():
    """
    Given a source contribution without a role
    When the model is built
    Then the role defaults to the generic Contributor role
    """
    contribution = SourceContribution(contributor=SourcePerson(**_minimal_contributor()))
    assert contribution.role == LocContributionRole.CONTRIBUTOR


def test_contribution_with_null_role_defaults_to_contributor():
    """
    Given a source contribution with an explicit null role
    When the model is built
    Then the role defaults to the generic Contributor role
    """
    contribution = SourceContribution(
        role=None,
        contributor=SourcePerson(**_minimal_contributor())
    )
    assert contribution.role == LocContributionRole.CONTRIBUTOR


def test_contribution_with_unknown_role_defaults_to_contributor():
    """
    Given a source contribution with a role URL outside the LoC relators vocabulary
    When the model is built
    Then the role defaults to the generic Contributor role
    """
    contribution = SourceContribution(
        role="https://id.loc.gov/vocabulary/relators/xxx.html",
        contributor=SourcePerson(**_minimal_contributor())
    )
    assert contribution.role == LocContributionRole.CONTRIBUTOR


def test_contribution_with_valid_role_is_kept():
    """
    Given a source contribution with a valid LoC role URL
    When the model is built
    Then the role maps to the corresponding relator
    """
    contribution = SourceContribution(
        role="https://id.loc.gov/vocabulary/relators/aut.html",
        contributor=SourcePerson(**_minimal_contributor())
    )
    assert contribution.role == LocContributionRole.AUTHOR
