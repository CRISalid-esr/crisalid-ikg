from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.documents.metadata_computation_service import MetadataComputationService
from app.services.source_contributors.source_contributor_mapping_service import \
    SourceContributorMappingService
from app.signals import document_updated, document_created, \
    document_unchanged, document_deleted


class DocumentService:
    """
    Service to handle operations on publication data
    """

    async def update_from_source_records(self, _, document_uid: str):
        """
        Recompute metadata for a document
        :param _: unused (for compatibility with signal handlers)
        :param document_uid: the document uid
        :return:
        """
        # fetch the source records to be merged

        sources_records = await self._get_source_records_of_document(document_uid)
        source_contributor_mapping_service = SourceContributorMappingService(
            source_records=sources_records, document_uid=document_uid)
        await source_contributor_mapping_service.update_contributions()
        # delegate the merge operation to the metadata computation service
        document = MetadataComputationService(sources_records).merge()
        document.uid = document_uid
        # set it explicitly to False for code clarity although it is the default value
        document.to_be_recomputed = False
        document.to_be_deleted = False
        # persist the merged document
        dao: DocumentDAO = cast(DocumentDAO, self._get_dao_factory().get_dao(Document))
        await dao.create_or_update_document(document)
        await self.signal_document_updated(document_uid)

    async def signal_document_updated(self, document_uid):
        """
        Signal that a document has been updated for all listeners to be notified
        :param document_uid:
        :return:
        """
        await document_updated.send_async(self, document_uid=document_uid)

    async def signal_document_created(self, document_uid):
        """
        Signal that a document has been created for all listeners to be notified
        :param document_uid:
        :return:
        """
        await document_created.send_async(self, document_uid=document_uid)

    async def signal_document_unchanged(self, document_uid):
        """
        Signal that a document has not been changed for all listeners to be notified
        :param document_uid:
        :return:
        """
        await document_unchanged.send_async(self, document_uid=document_uid)

    async def signal_document_deleted(self, document_uid):
        """
        Signal that a document has been deleted for all listeners to be notified
        :param document_uid:
        :return:
        """
        await document_deleted.send_async(self, document_uid=document_uid)

    async def _get_source_records_of_document(self, document_uid) -> list[
        SourceRecord]:
        source_record_dao = self._source_record_dao()
        sources_record_uids = await (
            source_record_dao.get_source_record_uids_by_document_uid(
                document_uid))
        return [await source_record_dao.get(source_record_uid) for source_record_uid in
                sources_record_uids]

    async def get_document(self, document_uid: str) -> Document | None:
        """
        Get a document by its uid
        :param document_uid:
        :return:
        """
        dao: DocumentDAO = self._document_dao()
        return await dao.get_document_by_uid(document_uid)

    async def get_document_uids(self) -> list[str]:
        """
        Get all document uids
        :return:
        """
        dao: DocumentDAO = self._document_dao()
        return await dao.get_document_uids()

    def _document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
        return dao

    def _source_record_dao(self) -> SourceRecordDAO:
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
        return dao

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
