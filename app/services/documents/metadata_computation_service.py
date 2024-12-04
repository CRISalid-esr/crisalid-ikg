from typing import List

from app.config import get_app_settings
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.conference_article import ConferenceArticle
from app.models.document_type import DocumentTypeEnum
from app.models.journal_article import JournalArticle
from app.models.proceedings import Proceedings
from app.models.source_records import SourceRecord
from app.models.textual_document import TextualDocument
from app.services.documents.merge_strategies.merge_strategy_factory import MergeStrategyFactory


class MetadataComputationService:
    """
    Service to handle operations on publication data
    """
    DOCUMENT_CLASS_BY_DOCUMENT_TYPE = {
        DocumentTypeEnum.ARTICLE: JournalArticle,
        DocumentTypeEnum.BOOK: Book,
        DocumentTypeEnum.CHAPTER: BookChapter,
        DocumentTypeEnum.CONFERENCE_PAPER: ConferenceArticle,
        DocumentTypeEnum.PROCEEDINGS: Proceedings
    }

    def __init__(self, source_records: List[SourceRecord]):
        """
        Constructor

        :param source_records: the source records to be merged
        """
        self.source_records = source_records
        self._elected_document_type = None

    def merge(self) -> TextualDocument:
        """
        Merge the source records into a single document
        :return:
        """
        return self._elected_strategy().merge()

    def _sort_source_records(self):
        self.source_records = sorted(self.source_records, key=lambda
            x: self._get_harvesters().index(
            x.harvester))

    def _elect_document_type(self) -> List[DocumentTypeEnum]:
        self._elected_document_type = next(
            (source_record.document_type for source_record in self.source_records if
             source_record.document_type and source_record.document_type != [
                 DocumentTypeEnum.UNKNOWN]),
            [DocumentTypeEnum.UNKNOWN]
        )

    def _textual_document_class(self):
        for document_type in self._elected_document_type:
            if document_type in self.DOCUMENT_CLASS_BY_DOCUMENT_TYPE:
                return self.DOCUMENT_CLASS_BY_DOCUMENT_TYPE[document_type]
        return TextualDocument

    def _elected_strategy(self):
        """
        Elect the appropriate policy for the document type
        :param document_type: The document type
        """
        self._sort_source_records()
        self._elect_document_type()
        expected_document_class = self._textual_document_class()
        for strategy in self._get_strategies():
            document_type_values = [document_type.value for document_type in
                                    self._elected_document_type]
            if any(doc_type in strategy['types'] for doc_type in document_type_values):
                return self._instantiate_strategy(expected_document_class, strategy)
        default_strategy = next(
            (strategy for strategy in self._get_strategies() if 'default' in strategy['types']),
            None
        )
        assert default_strategy is not None, "No default strategy found"
        return self._instantiate_strategy(expected_document_class, default_strategy)

    def _instantiate_strategy(self, expected_document_class:type, strategy: dict):
        return MergeStrategyFactory[expected_document_class].create_strategy(
            strategy_type=MergeStrategyFactory.StrategyType(strategy['type']),
            source_records=self.source_records,
            parameters=strategy.get("parameters", {}),
            document_class=expected_document_class
        )

    def _get_policies(self):
        return get_app_settings().publication_source_policies

    def _get_strategies(self):
        return self._get_policies()['strategies']

    def _get_harvesters(self):
        return self._get_policies()['harvesters']
