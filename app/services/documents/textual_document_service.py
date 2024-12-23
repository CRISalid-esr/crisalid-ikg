from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.documents.metadata_computation_service import MetadataComputationService


class TextualDocumentService:
    """
    Service to handle operations on publication data
    """

    async def update_from_source_records(self, _, textual_document_uid: str):
        """
        Recompute metadata for a textual document
        :param _: unused (for compatibility with signal handlers)
        :param textual_document_uid: the textual document uid
        :return:
        """
        # fetch the source records to be merged
        dao = await self._source_record_dao()
        sources_record_uids = await dao.get_source_record_uids_by_textual_document_uid(
            textual_document_uid)
        sources_records = []
        for source_record_uid in sources_record_uids:
            source_record = await dao.get(source_record_uid)
            sources_records.append(source_record)
        # delegate the merge operation to the metadata computation service
        document = MetadataComputationService(sources_records).merge()
        document.uid = textual_document_uid
        # set it explicitly to False for code clarity although it is the default value
        document.to_be_recomputed = False
        document.to_be_deleted = False
        # persist the merged document
        dao: DocumentDAO = cast(DocumentDAO, self._get_dao_factory().get_dao(Document))
        await dao.create_or_update_textual_document(document)

    async def _source_record_dao(self) -> SourceRecordDAO:
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
        return dao

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
