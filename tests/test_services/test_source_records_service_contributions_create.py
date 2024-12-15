import pytest

from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


@pytest.mark.current
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
