from itertools import combinations
from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.document_publication_channel import DocumentPublicationChannel
from app.models.source_records import SourceRecord
from app.services.documents.metadata_computation_service import MetadataComputationService
from app.services.journals.journal_service import JournalService
from app.services.source_contributors.source_contributor_mapping_service import \
    SourceContributorMappingService
from app.services.source_records.equivalence_service import EquivalenceService
from app.signals import document_updated, document_created, \
    document_unchanged, document_deleted


class DocumentService:
    """
    Service to handle operations on publication data
    """

    async def update_from_source_records(self, _, document_uid: str):
        """
        Recompute metadata for an existing document
        :param _: unused (for compatibility with signal handlers)
        :param document_uid: the document uid
        :return:
        """
        to_be_deleted = not await self._compute_document_from_source_records(document_uid)
        if to_be_deleted:
            await self.signal_document_deleted(document_uid)
        else:
            await self.signal_document_updated(document_uid)

    async def create_from_source_records(self, _, document_uid: str):
        """
        Recompute metadata for a newly created document
        :param _: unused (for compatibility with signal handlers)
        :param document_uid: the document uid
        :return:
        """
        # fetch the source records to be merged
        await self._compute_document_from_source_records(document_uid)
        await self.signal_document_created(document_uid)

    async def merge_documents(self, document_uids: set[str]) -> None:
        """
        Merge a set of documents by asserting equivalences between their source records.
        Steps:
          1) Fetch source-record UIDs for each document UID (list of sets).
          2) Call SourceRecordDAO.create_asserted_equivalences(...) with that structure.
          3) Pick any source-record UID and trigger EquivalenceService.update_source_records(...)
        """
        if not isinstance(document_uids, set) or len(document_uids) < 2:
            raise ValueError("merge_documents expects a set of at least two document UIDs.")

        source_record_dao = self._source_record_dao()

        # 1) Collect source-record UIDs per document (list of sets)
        per_document_source_sets: list[set[str]] = []
        for doc_uid in document_uids:
            src_uids = await source_record_dao.get_source_record_uids_by_document_uid(doc_uid)
            per_document_source_sets.append(set(src_uids))

        # 2) For each unordered pair of sets, assert equivalences
        for set1, set2 in combinations(per_document_source_sets, 2):
            if set1 and set2:
                await source_record_dao.create_asserted_equivalence_relationships(set1, set2)

        # 3) Take any source-record UID and trigger source record clusters update
        representative_uid: str | None = None
        for group in per_document_source_sets:
            if group:
                representative_uid = next(iter(group))
                break

        if representative_uid is None:
            # Nothing to trigger if there are no source records at all
            return

        svc = EquivalenceService()
        await svc.update_source_record(self, representative_uid)

    async def _compute_document_from_source_records(self, document_uid) -> bool:
        """
        Compute the metadata of a document from its source records
        :param document_uid:
        :return: False if the document should be deleted (i.e. has no source records)
        """
        sources_records = await self._get_source_records_of_document(document_uid)
        source_contributor_mapping_service = SourceContributorMappingService(
            source_records=sources_records, document_uid=document_uid)
        await source_contributor_mapping_service.update_contributions()
        # delegate the merge operation to the metadata computation service
        document = MetadataComputationService(sources_records).merge()
        document.uid = document_uid
        # set it explicitly to False for code clarity although it is the default value
        document.to_be_recomputed = False
        to_be_deleted = len(sources_records) == 0
        document.to_be_deleted = to_be_deleted
        if to_be_deleted:
            return False
        publication_channel: DocumentPublicationChannel = (
            await JournalService().compute_document_publication_channel(
                document_uid=document_uid,
                source_records=sources_records))
        if publication_channel is not None:
            document.publication_channels.append(publication_channel)
        # persist the merged document
        dao: DocumentDAO = cast(DocumentDAO, self._get_dao_factory().get_dao(Document))
        await dao.create_or_update_document(document)
        # import dynamically to avoid circular imports
        # pylint: disable=import-outside-toplevel,cyclic-import
        from app.services.changes.change_service import ChangeService
        await ChangeService().apply_changes_to_node(document_uid)
        return True

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
