from typing import cast

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.document_publication_channel import DocumentPublicationChannel
from app.models.journal import Journal
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.documents.document_service import DocumentService
from app.services.journals.journal_service import JournalService
from app.services.source_records.equivalence_service import EquivalenceService
from app.services.source_records.source_record_service import SourceRecordService
from app.signals import source_journal_created, source_journal_updated, source_record_created, \
    source_record_updated


@pytest.fixture(autouse=True)
def setup_services_with_signals():
    """
    Setup fixture to connect the journal and equivalence services to the source record signals.
    :return:
    """
    journal_service = JournalService()
    equivalence_service = EquivalenceService()

    # Connect journal service signals
    source_journal_created.connect(journal_service.link_journal_identifiers)
    source_journal_updated.connect(journal_service.link_journal_identifiers)

    # Connect equivalence service signals
    source_record_created.connect(equivalence_service.update_source_record)
    source_record_updated.connect(equivalence_service.update_source_record)

    yield

    # Disconnect journal service signals
    source_journal_created.disconnect(journal_service.link_journal_identifiers)
    source_journal_updated.disconnect(journal_service.link_journal_identifiers)

    # Disconnect equivalence service signals
    source_record_created.disconnect(equivalence_service.update_source_record)
    source_record_updated.disconnect(equivalence_service.update_source_record)


async def test_merge_documents_with_journal_information(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Test that when 2 equivalent source records come with journal issn pointing to the same journal,
    and with complementary information (number, issue), journal information is merged
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model,
            identifier_used=default_identifier_used
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model,
        identifier_used=default_identifier_used
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.publication_channels is not None
    assert len(document.publication_channels) == 1
    publication_channel = document.publication_channels[0]
    assert publication_channel is not None
    assert isinstance(publication_channel, DocumentPublicationChannel)
    assert publication_channel.pages == ''
    assert publication_channel.volume == '134'
    assert publication_channel.issue == '1'
    journal = publication_channel.publication_channel
    assert journal is not None
    assert isinstance(journal, Journal)
    assert journal.uid == "issn-l-1090-0241"
    assert journal.titles == ["Journal of Geotechnical and Geoenvironmental Engineering"]
    assert journal.acronym == []
    assert journal.publisher == "American Society of Civil Engineers v2"


async def test_merge_documents_with_inconsistent_journal_information(
        caplog,  # pylint: disable=unused-argument
        hal_article_with_inconsistent_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Test that when 2 equivalent source records with journal information come but the first one (
    from hal) has issn identifier pointing to 2 different journals, the journal information is taken
    from the second one (from open alex) and the journal information is not merged
    :param hal_article_with_journal_1_persisted_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal__persisted_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    source_record_service = SourceRecordService()
    hal_article_with_inconsistent_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_inconsistent_journal_1_pydantic_model,
            persisted_person_f_pydantic_model,
            identifier_used=default_identifier_used
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model,
        identifier_used=default_identifier_used
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_inconsistent_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.publication_channels is not None
    assert len(document.publication_channels) == 1
    publication_channel = document.publication_channels[0]
    assert publication_channel is not None
    assert isinstance(publication_channel, DocumentPublicationChannel)
    assert publication_channel.pages == ''
    assert publication_channel.volume == ''
    assert publication_channel.issue == '1'
    journal = publication_channel.publication_channel
    assert journal is not None
    assert isinstance(journal, Journal)
    assert journal.uid == "issn-l-1090-0241"
    assert journal.titles == ["Journal of Geotechnical and Geoenvironmental Engineering"]
    assert journal.acronym == []
    assert journal.publisher == "American Society of Civil Engineers v2"
    assert ("Multiple journals found for source journal hal-0000-0000, "
            "ignoring this source record.") in caplog.text


async def test_merge_documents_with_different_journal_information(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_2_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Test that when 2 equivalent source records with journal information come but the first one (
    from hal) has issn identifier pointing to a different journal than the second one
    (from open alex),  the journal information is taken from the preferred one (Hal).
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_2_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model,
            identifier_used=default_identifier_used
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_2_pydantic_model,
        persisted_person_f_pydantic_model,
        identifier_used=default_identifier_used
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    publication_channel = document.publication_channels[0]
    assert publication_channel is not None
    assert isinstance(publication_channel, DocumentPublicationChannel)
    assert publication_channel.pages == ''
    assert publication_channel.volume == '134'
    assert publication_channel.issue == ''
    journal = publication_channel.publication_channel
    assert journal is not None
    assert isinstance(journal, Journal)
    assert journal.uid == "issn-l-1090-0241"
    assert journal.titles == ["Journal of Geotechnical and Geoenvironmental Engineering"]
    assert journal.acronym == []
    assert journal.publisher == "American Society of Civil Engineers v1"


async def test_merge_documents_with_journal_information_changes(
        test_app,  # pylint: disable=unused-argument
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        hal_article_with_journal_2_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Test that when a document is updated with a new journal information,
    the journal information is updated accordingly.
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param hal_article_with_journal_2_pydantic_model: Pydantic SourceRecord object from
    HAL with new journal information and DOI identifier
    :param persisted_person_f_pydantic_model: Pydantic Person object to ensure
    the document is created with a person
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model,
            identifier_used=default_identifier_used
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model,
        identifier_used=default_identifier_used
    )

    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.publication_channels is not None
    assert len(document.publication_channels) == 1
    publication_channel = document.publication_channels[0]
    assert publication_channel is not None
    assert isinstance(publication_channel, DocumentPublicationChannel)
    assert publication_channel.pages == ''
    assert publication_channel.volume == '134'
    assert publication_channel.issue == '1'
    journal = publication_channel.publication_channel
    assert journal is not None
    assert isinstance(journal, Journal)
    assert journal.uid == "issn-l-1090-0241"
    assert journal.titles == ["Journal of Geotechnical and Geoenvironmental Engineering"]
    assert journal.acronym == []
    assert journal.publisher == "American Society of Civil Engineers v2"
    await source_record_service.update_source_record(
        hal_article_with_journal_2_pydantic_model,
        persisted_person_f_pydantic_model,
        identifier_used=default_identifier_used
    )
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.publication_channels is not None
    assert len(document.publication_channels) == 1
    publication_channel = document.publication_channels[0]
    assert publication_channel is not None
    assert isinstance(publication_channel, DocumentPublicationChannel)
    assert publication_channel.pages == ''
    assert publication_channel.volume == '134'
    assert publication_channel.issue == ''
    journal = publication_channel.publication_channel
    assert journal is not None
    assert isinstance(journal, Journal)
    assert journal.uid == "issn-l-0007-4217"
    assert journal.titles == ["Sample Journal Title"]
    assert journal.acronym == []
    assert journal.publisher == "Publisher of sample journal"
