from typing import List

import pytest

from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.document_type import DocumentTypeEnum
from app.models.harvesters import Harvester
from app.models.journal_article import JournalArticle
from app.models.proceedings import Proceedings
from app.models.source_records import SourceRecord
from app.services.documents.merge_strategies.global_richest_merge_strategy import \
    GlobalRichestMergeStrategy
from app.services.documents.merge_strategies.richest_by_field_merge_strategy import \
    RichestByFieldMergeStrategy
from app.services.documents.merge_strategies.source_order_merge_strategy import \
    SourceOrderMergeStrategy
from app.services.documents.metadata_computation_service import MetadataComputationService


async def test_recompute_document_from_three_documents(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord
) -> None:
    """
    Test that when 3 source_recorded are registered as equivalent, the document is
    recomputed from their metadata
    :param source_record_id_doi_1_pydantic_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_pydantic_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_pydantic_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    service_under_test = MetadataComputationService([
        source_record_id_doi_1_pydantic_model,
        source_record_id_hal_1_pydantic_model,
        source_record_id_doi_1_hal_1_pydantic_model
    ])
    document = service_under_test.merge()
    assert document is not None


@pytest.mark.parametrize(
    "harvester_order,"
    "source_document_types,"
    "expected_document_type,"
    "expected_document_class,"
    "expected_strategy",
    [
        (["hal", "scanr", "openalex"],
         [DocumentTypeEnum.UNKNOWN, DocumentTypeEnum.ARTICLE, DocumentTypeEnum.BOOK],
         DocumentTypeEnum.ARTICLE, JournalArticle, GlobalRichestMergeStrategy),
        (["scopus", "scanr", "openalex"], [DocumentTypeEnum.BOOK, DocumentTypeEnum.UNKNOWN,
                                           DocumentTypeEnum.ARTICLE],
         DocumentTypeEnum.BOOK, Book, SourceOrderMergeStrategy),
        (["idref", "hal", "scanr"], [DocumentTypeEnum.ARTICLE, DocumentTypeEnum.UNKNOWN,
                                     DocumentTypeEnum.BOOK],
         DocumentTypeEnum.ARTICLE, JournalArticle, GlobalRichestMergeStrategy),
        (["scopus", "openalex", "hal"], [DocumentTypeEnum.ARTICLE, DocumentTypeEnum.BOOK,
                                         DocumentTypeEnum.UNKNOWN],
         DocumentTypeEnum.ARTICLE, JournalArticle, GlobalRichestMergeStrategy),
        (["idref", "hal", "scanr"], [DocumentTypeEnum.PROCEEDINGS, DocumentTypeEnum.UNKNOWN,
                                     DocumentTypeEnum.ARTICLE],
         DocumentTypeEnum.PROCEEDINGS, Proceedings, RichestByFieldMergeStrategy),
        (["scanr", "scopus", "hal"], [DocumentTypeEnum.CHAPTER, DocumentTypeEnum.ARTICLE,
                                      DocumentTypeEnum.UNKNOWN],
         DocumentTypeEnum.CHAPTER, BookChapter, GlobalRichestMergeStrategy)
    ])


# pylint: disable=too-many-arguments
async def test_merge_document_with_inconsistent_types(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord,
        harvester_order: List[str],
        source_document_types: List[DocumentTypeEnum],
        expected_document_type: DocumentTypeEnum,
        expected_document_class: type,
        expected_strategy: type
) -> None:
    """
    Test that when 3 source records with inconsistent types are merged,
    the elected type is elected following the harvesters priority order
    :param source_record_id_doi_1_pydantic_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_pydantic_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_pydantic_model: Pydantic SourceRecord object with both
    :param harvester_order: The source harvesters of the provided source records
    :param source_document_types: The document types of the provided source records
    :param expected_document_type: The expected elected document type
    :param expected_document_class: The expected elected document class
    """
    # Hal is the first harvester in the priority order, but the document type is unknown
    source_record_id_hal_1_pydantic_model.harvester = Harvester(harvester_order[0])
    source_record_id_hal_1_pydantic_model.document_type = [source_document_types[0]]
    # Scanr is the second harvester in the priority order, and the document type
    # is set, so it should be elected
    source_record_id_doi_1_pydantic_model.harvester = Harvester(harvester_order[1])
    # OpenAlex is the last harvester in the priority order, so its document type
    # should be ignored
    source_record_id_doi_1_pydantic_model.document_type = [source_document_types[1]]
    source_record_id_doi_1_hal_1_pydantic_model.harvester = Harvester(harvester_order[2])
    source_record_id_doi_1_hal_1_pydantic_model.document_type = [source_document_types[2]]
    # merge the source records
    service_under_test = MetadataComputationService([
        source_record_id_doi_1_pydantic_model,
        source_record_id_hal_1_pydantic_model,
        source_record_id_doi_1_hal_1_pydantic_model
    ])
    document = service_under_test.merge()
    assert document is not None
    assert (len(service_under_test.get_elected_document_type())  # pylint: disable=protected-access
            == 1)
    assert (service_under_test.get_elected_document_type()[0]  # pylint: disable=protected-access
            == expected_document_type)
    assert isinstance(service_under_test.get_elected_strategy(),
                      expected_strategy)  # pylint: disable=protected-access
    assert isinstance(document, expected_document_class)
