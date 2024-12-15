
from app.models.loc_contribution_role import LocContributionRole
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_source_record_with_contributions(
        # test_app,  # pylint: disable=unused-argument
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
    contribution_1 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100002'),
        None
    )
    assert contribution_1
    assert contribution_1.rank == 1
    assert contribution_1.role == LocContributionRole.WRITER_OF_INTRODUCTION
    assert contribution_1.contributor.name == 'Jean Martin'
    contribution_2 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100003'),
        None
    )
    assert contribution_2
    assert contribution_2.rank == 2
    assert contribution_2.role == LocContributionRole.AUTHOR
    assert contribution_2.contributor.name == 'Charlie Bernard'
    contribution_3 = next(
        (c for c in fetched_source_record.contributions if c.contributor.uid == 'hal-100004'),
        None
    )
    assert contribution_3
