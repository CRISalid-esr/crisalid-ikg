# pylint: disable=duplicate-code
from app.models.harvesting_sources import HarvestingSource
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.models.source_organizations import SourceOrganization
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_source_record_with_contributions(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        hal_chapter_a_source_record_pydantic_model: SourceRecord
) -> None:
    """
    Given a persisted person pydantic model and a non persisted source record pydantic model
    When the source record is added to the graph
    Then the source record can be read from the graph

    :param persisted_person_a_pydantic_model:
    :param hal_chapter_a_source_record_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=hal_chapter_a_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    assert await service.source_record_exists(hal_chapter_a_source_record_pydantic_model.uid)
    fetched_source_record = await service.get_source_record(
        hal_chapter_a_source_record_pydantic_model.uid)
    assert fetched_source_record
    assert fetched_source_record.contributions
    assert len(fetched_source_record.contributions) == 4
    contribution_0 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100001'),
        None
    )
    assert contribution_0
    assert contribution_0.rank == 0
    assert contribution_0.role == LocContributionRole.AUTHOR
    assert contribution_0.contributor.name == 'Alice Dupont'
    assert len(contribution_0.affiliations) == 1
    assert contribution_0.affiliations[0].source == HarvestingSource.HAL
    assert contribution_0.affiliations[0].source_identifier == '2001'
    assert contribution_0.affiliations[0].name == 'Université Anonyme'
    assert (contribution_0.affiliations[0].type ==
            SourceOrganization.SourceOrganisationType.INSTITUTION)
    assert len(contribution_0.affiliations[0].identifiers) == 4
    assert any(
        i.type == 'isni' and i.value == '000000012345678X'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'hal' and i.value == '2001'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'idref' and i.value == '123456789'
        for i in contribution_0.affiliations[0].identifiers
    )
    assert any(
        i.type == 'ror' and i.value == 'https://ror.org/000000000'
        for i in contribution_0.affiliations[0].identifiers
    )
    contribution_1 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100002'),
        None
    )
    assert contribution_1
    assert contribution_1.rank == 1
    assert contribution_1.role == LocContributionRole.WRITER_OF_INTRODUCTION
    assert contribution_1.contributor.name == 'Jean Martin'
    assert len(contribution_1.affiliations) == 0
    contribution_2 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100003'),
        None
    )
    assert contribution_2
    assert contribution_2.rank == 2
    assert contribution_2.role == LocContributionRole.AUTHOR
    assert contribution_2.contributor.name == 'Charlie Bernard'
    assert len(contribution_2.affiliations) == 3
    assert any(
        a.source == HarvestingSource.HAL and a.source_identifier == '3001'
        and a.name == 'Institut de Technologie Anonyme'
        for a in contribution_2.affiliations
    )
    assert any(
        a.source == HarvestingSource.HAL and a.source_identifier == '3003'
        and a.name == 'Groupe de Recherche Anonyme'
        for a in contribution_2.affiliations
    )
    assert any(
        a.source == HarvestingSource.HAL and a.source_identifier == '3002'
        and a.name == 'Laboratoire Interdisciplinaire'
        for a in contribution_2.affiliations
    )
    contribution_3 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100004'),
        None
    )
    assert contribution_3
    assert contribution_3.rank == 3
    assert contribution_3.role == LocContributionRole.TRANSLATOR
    assert contribution_3.contributor.name == 'Marie Lefèvre'
    assert len(contribution_3.affiliations) == 0
