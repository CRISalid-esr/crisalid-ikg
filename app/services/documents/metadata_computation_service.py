from typing import List

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.conference_article import ConferenceArticle
from app.models.document import Document
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

    def __init__(self):
        self.textual_document_uid = None
        self.source_records: List[SourceRecord] = []
        self.document_type: DocumentTypeEnum = DocumentTypeEnum.UNKNOWN

    async def recompute_metadata(self, _, textual_document_uid: str):
        """
        Recompute metadata for a publication
        :param publication_uid: publication uid
        :return:
        """
        self.textual_document_uid = textual_document_uid
        await self._fetch_publication_sources()
        strategy = self._elect_strategy()
        document = strategy.merge()
        # set it explicitly to False for code clarity although it is the default value
        document.to_be_recomputed = False
        document.to_be_deleted = False
        dao: DocumentDAO = self._get_dao_factory().get_dao(Document)
        await dao.create_or_update_textual_document(document)

    async def _sort_source_records(self):
        self.source_records = sorted(self.source_records, key=lambda
            x: self._get_harvesters().index(
            x.harvester))

    async def _fetch_publication_sources(self) -> List[SourceRecord]:
        """
        Get a source record from the graph database
        :param source_record_uid: source record uid
        :return: Pydantic SourceRecord object
        """
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        self.source_records = await dao.get_source_records_by_textual_document_uid(
            self.textual_document_uid)

    def _choose_document_type(self) -> List[DocumentTypeEnum]:
        self.document_type = next(
            (source_record.document_type for source_record in self.source_records if
             source_record.document_type),
            [DocumentTypeEnum.UNKNOWN]
        )

    def _textual_document_class(self):
        for document_type in self.document_type:
            if document_type in self.DOCUMENT_CLASS_BY_DOCUMENT_TYPE:
                return self.DOCUMENT_CLASS_BY_DOCUMENT_TYPE[document_type]
        return TextualDocument

    def _elect_strategy(self):
        """
        Elect the appropriate policy for the document type
        :param document_type: The document type
        """
        self._sort_source_records()
        self._choose_document_type()
        expected_document_class = self._textual_document_class()
        for strategy in self._get_strategies():
            document_type_values = [document_type.value for document_type in self.document_type]
            if any(doc_type in strategy['types'] for doc_type in document_type_values):
                strategy = (MergeStrategyFactory[expected_document_class].create_strategy(
                    strategy_type=MergeStrategyFactory.StrategyType(strategy['type']),
                    source_records=self.source_records,
                    parameters=strategy.get("parameters", {}),
                    document_class=expected_document_class,
                    textual_document_uid=self.textual_document_uid
                ))
                return strategy

    def _get_policies(self):
        return get_app_settings().publication_source_policies

    def _get_strategies(self):
        return self._get_policies()['strategies']

    def _get_harvesters(self):
        return self._get_policies()['harvesters']

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
