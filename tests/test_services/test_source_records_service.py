from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_source_record(persisted_person_pydantic_model: Person,
                                    scanr_thesis_source_record_pydantic_model: SourceRecord
                                    ) -> None:
    """
    Given a persisted person pydantic model and a non persisted source record pydantic model
    When the source record is added to the graph
    Then the source record can be read from the graph
    :param person_pydantic_model:
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_thesis_source_record_pydantic_model,
                                       harvested_for=persisted_person_pydantic_model)
    fetched_source_record = await service.get_source_record(
        scanr_thesis_source_record_pydantic_model.uid)
    assert fetched_source_record.uid == scanr_thesis_source_record_pydantic_model.uid
    assert fetched_source_record.source_identifier == \
           scanr_thesis_source_record_pydantic_model.source_identifier
    assert fetched_source_record.harvester == \
           scanr_thesis_source_record_pydantic_model.harvester
    for title in scanr_thesis_source_record_pydantic_model.titles:
        assert any(
            fetched_title.language == title.language and fetched_title.value == title.value for
            fetched_title in fetched_source_record.titles)
    for identifier in scanr_thesis_source_record_pydantic_model.identifiers:
        assert any(
            fetched_identifier.type ==
            identifier.type and fetched_identifier.value == identifier.value
            for fetched_identifier in fetched_source_record.identifiers)
    for abstract in scanr_thesis_source_record_pydantic_model.abstracts:
        assert any(
            fetched_abstract.language == abstract.language
            and fetched_abstract.value == abstract.value
            for fetched_abstract in fetched_source_record.abstracts)
