from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_multiple_source_records_with_common_id_for_multiple_person(
        persisted_person_a_pydantic_model: Person,
        persisted_person_b_pydantic_model: Person,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        hal_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_a_source_record_pydantic_model: SourceRecord
) -> None:
    """
    Given 3 source records with common hal identifier and created for different persons,
    When the source records are added to the graph
    Then the source records can be read and should be related to each other with a relationship.
    """
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    await source_record_service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)

    await source_record_service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
