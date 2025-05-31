from datetime import datetime
from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.document_publication_channel import DocumentPublicationChannel
from app.models.journal import Journal
from app.models.journal_article import JournalArticle
from app.models.source_records import SourceRecord
from app.services.documents.document_service import DocumentService
from app.services.source_records.equivalence_service import EquivalenceService
from app.signals import source_record_created, source_record_updated, \
    document_sources_changed


async def test_update_document(
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,  # pylint: disable=unused-argument
        source_record_id_doi_1_hal_1_persisted_model: SourceRecord
        # pylint: disable=unused-argument
) -> None:
    """
    Test that when 3 source_recorded are registered as equivalent, the document is
    recomputed from their metadata
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_persisted_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_hal_1_persisted_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    with source_record_updated.muted():
        with source_record_created.muted():
            with document_sources_changed.muted():
                equivalence_service = EquivalenceService()
                factory = AbstractDAOFactory().get_dao_factory("neo4j")
                document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
                # update any of the source records, does not matter which one
                await equivalence_service.update_source_record(
                    None,
                    source_record_id_doi_1_persisted_model.uid)

                document = await document_dao.get_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is True
                await DocumentService().update_from_source_records(
                    None,
                    document_uid=document.uid)
                document = await document_dao.get_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is False
                assert len(document.titles) == 1
                assert document.titles[0].value == "Example Article with DOI and HAL"
                assert document.publication_date is not None
                assert document.publication_date == "2019-02"
                assert isinstance(document.publication_date_start, datetime)
                assert isinstance(document.publication_date_end, datetime)
                assert document.publication_date_end.isoformat() == "2019-02-28T23:59:59"
                assert document.publication_date_start.isoformat() == "2019-02-01T00:00:00"
                assert isinstance(document, JournalArticle)
                assert document.type == "JournalArticle"
                assert len(document.subjects) == 4
                assert all(subject.uid in [
                    "http://www.idref.fr/concept-a/id",
                    "http://www.idref.fr/concept-b/id",
                    "http://www.idref.fr/concept-d/id",
                    "http://www.idref.fr/concept-e/id"
                ] for subject in document.subjects)


async def test_merge_documents_with_journal_information(
        test_app,  # pylint: disable=unused-argument
        hal_article_with_journal_1_persisted_model,
        open_alex_article_with_journal_1_persisted_model # pylint: disable=unused-argument
) -> None:
    """
    Test that when 2 equivalent source records come with journal issn pointing to the same journal,
    and with complementary information (number, issue), journal information is merged
    :param hal_article_with_journal_1_persisted_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_persisted_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    assert hal_article_with_journal_1_persisted_model is not None
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
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
