from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_source_record(persisted_person_a_pydantic_model: Person,
                                    scanr_thesis_source_record_pydantic_model: SourceRecord
                                    ) -> None:
    """
    Given a persisted person pydantic model and a non persisted source record pydantic model
    When the source record is added to the graph
    Then the source record can be read from the graph
    :param person_a_pydantic_model:
    :param scanr_thesis_source_record_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_thesis_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
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
    # only works if concepts have URIs
    for subject in scanr_thesis_source_record_pydantic_model.subjects:
        assert any(
            fetched_subject.uri == subject.uri for fetched_subject in
            fetched_source_record.subjects)


async def test_create_two_source_records_with_same_concepts(
        persisted_person_a_pydantic_model: Person,
        idref_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord
) -> None:
    """
    Given a persisted person Pydantic model,
    When two source record are added for this person with concepts in common,
    Then the records should share the concepts in common

    :param persisted_person_a_pydantic_model:
    :param idref_record_with_person_a_as_contributor_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=idref_record_with_person_a_as_contributor_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_idref_source_record = await service.get_source_record(
        idref_record_with_person_a_as_contributor_pydantic_model.uid)
    assert (
            fetched_idref_source_record.uid ==
            idref_record_with_person_a_as_contributor_pydantic_model.uid
    )
    await service.create_source_record(
        source_record=scanr_record_with_person_a_as_contributor_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_scanr_source_record = await service.get_source_record(
        scanr_record_with_person_a_as_contributor_pydantic_model.uid)
    assert (
            fetched_scanr_source_record.uid ==
            scanr_record_with_person_a_as_contributor_pydantic_model.uid
    )
    assert any(
        (concept in fetched_scanr_source_record.subjects for concept in
         fetched_idref_source_record.subjects)
    )
