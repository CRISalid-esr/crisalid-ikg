from typing import List

import pytest

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier
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


async def test_journal_from_scanr_article(
        scanr_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
):
    """
        Given a valid source record model representing an article harvested from ScanR
        When asked for different field values
        Then the values should be returned correctly
        """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_article_a_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    fetched_source_record = await service.get_source_record(
        scanr_article_a_source_record_pydantic_model.uid)
    assert fetched_source_record.source_identifier == "doi10.3847/1538-4357/ad0cc0"
    assert fetched_source_record.harvester == "ScanR"
    issue = fetched_source_record.issue
    assert issue.source == "ScanR"
    assert issue.source_identifier == "the_astrophysical_journal-ScanR"
    journal = issue.journal
    assert journal.source == "ScanR"
    assert journal.source_identifier == \
           "0004-637X-1538-4357-the_astrophysical_journal-american_astronomical_society-ScanR"
    assert journal.publisher == "American Astronomical Society"
    assert "The Astrophysical Journal" in journal.titles
    journal_identifiers: List[JournalIdentifier] = journal.identifiers
    assert any(identifier.value == "0004-637X" and identifier.type == JournalIdentifierType.ISSN
               for identifier in journal_identifiers)
    assert any(identifier.value == "1538-4357" and identifier.type == JournalIdentifierType.ISSN
               for identifier in journal_identifiers)


@pytest.mark.current
async def test_two_scanr_articles_from_same_journal_and_person(
        scanr_article_a_source_record_pydantic_model: SourceRecord,
        scanr_article_b_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
):
    """
    Given two source records from the same issue and journal and harvested for the same person
    When the records are added two the graph
    Then they should share the same journal
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_article_a_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    await service.create_source_record(source_record=scanr_article_b_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)

    fetched_source_record_a = await service.get_source_record(
        scanr_article_a_source_record_pydantic_model.uid)
    fetched_source_record_b = await service.get_source_record(
        scanr_article_b_source_record_pydantic_model.uid)
    assert fetched_source_record_a.issue.journal.uid == fetched_source_record_b.issue.journal.uid
    assert fetched_source_record_a.issue.journal.source == \
           fetched_source_record_b.issue.journal.source
    assert fetched_source_record_a.issue.journal.source_identifier == \
           fetched_source_record_b.issue.journal.source_identifier
    assert fetched_source_record_a.issue.journal.publisher == \
           fetched_source_record_b.issue.journal.publisher
    # sort and compare titles
    assert sorted(fetched_source_record_a.issue.journal.titles) == sorted(
        fetched_source_record_b.issue.journal.titles)
    # compare journal identifiers
    assert len(fetched_source_record_a.issue.journal.identifiers) == len(
        fetched_source_record_b.issue.journal.identifiers)
    for identifier_a in fetched_source_record_a.issue.journal.identifiers:
        assert any(
            identifier_a.value == identifier_b.value and identifier_a.type == identifier_b.type
            for identifier_b in fetched_source_record_b.issue.journal.identifiers)
    # compare fetched_source_record_a.issue with fetched_source_record_b.issue
    assert fetched_source_record_a.issue.source == fetched_source_record_b.issue.source
    assert fetched_source_record_a.issue.source_identifier == \
           fetched_source_record_b.issue.source_identifier
    assert fetched_source_record_a.issue.volume == fetched_source_record_b.issue.volume
    assert fetched_source_record_a.issue.number == fetched_source_record_b.issue.number
    assert fetched_source_record_a.issue.rights == fetched_source_record_b.issue.rights
    assert fetched_source_record_a.issue.date == fetched_source_record_b.issue.date
