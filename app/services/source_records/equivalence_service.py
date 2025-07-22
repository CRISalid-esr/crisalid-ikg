from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.signals import document_sources_changed, document_created_from_sources

MAX_EQUIVALENCES_RECURSION_LEVEL = 100


class EquivalenceService:
    """
    Service to handle equivalence relationships between source records
    """

    def __init__(self):
        self.source_records_to_update_uids = []

    async def update_source_record(self, _, source_record_id) -> None:
        """
        Update a source record with the given id
        :param _:
        :param source_record_id:
        :return:
        """
        logger.debug(f"beginning to update source record with id {source_record_id}")
        self.source_records_to_update_uids.append(source_record_id)
        await self._update_inferred_equivalence_relationships()

    async def _update_inferred_equivalence_relationships(self, recursion_level: int = 0) -> None:
        """
        Recursively update the inferred equivalence relationships between source records
        :return:
        """
        if not self.source_records_to_update_uids:
            return
        if recursion_level > MAX_EQUIVALENCES_RECURSION_LEVEL:
            logger.error("Recursion limit reached while updating inferred equivalence "
                         "relationships for remaining source records: "
                         f"{self.source_records_to_update_uids}")
            return
        # Pop the first source record from the list and use it as the origin of the whole algorithm
        obsolete_source_record_uid = self.source_records_to_update_uids.pop(0)
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        # Fetch the weakly connected graph of source records that share identifiers with the origin
        sr_with_shared_identifier_uids = [obsolete_source_record_uid]
        sr_with_shared_identifier_uids.extend(
            await (
                dao.get_source_records_with_shared_identifier_uids(
                    obsolete_source_record_uid)
            ))
        sr_with_shared_identifier_uids = list(set(sr_with_shared_identifier_uids))
        # Fetch the weakly connected graph of source records that are inferred to be equivalent to
        # one of the source records in the weakly connected graph of shared identifiers
        existing_inferred_equiv_sr_uids = [obsolete_source_record_uid]
        for source_record_uid in sr_with_shared_identifier_uids:
            existing_inferred_equiv_sr_uids.extend(
                await dao.get_source_records_equivalent_uids(
                    source_record_uid, SourceRecordDAO.EquivalenceType.INFERRED))
        existing_inferred_equiv_sr_uids = list(set(existing_inferred_equiv_sr_uids))
        # The set of source records that belong to the weakly connected graph of inferred
        # equivalences but not to the weakly connected graph of shared identifiers
        # should lose their inferred equivalence relationships
        obsolete_inferred_equiv_sr_uids = [x for x in existing_inferred_equiv_sr_uids if
                                           x not in sr_with_shared_identifier_uids]
        for obsolete_inferred_equiv_sr_uid in obsolete_inferred_equiv_sr_uids:
            await dao.delete_inferred_equivalence_relationships(
                source_record_uid=obsolete_inferred_equiv_sr_uid,
                target_source_record_uids=sr_with_shared_identifier_uids)
            # Add any detached source records to the list of records to update
            self.source_records_to_update_uids.append(obsolete_inferred_equiv_sr_uid)
        await dao.create_inferred_equivalence_relationships(
            sr_with_shared_identifier_uids)
        # Handle attached publications
        await self._update_documents(obsolete_source_record_uid)
        # Loop until the source_records_to_update list is empty
        await self._update_inferred_equivalence_relationships()

    async def _update_documents(self, origin_source_record_uid) -> None:
        """
        Update the attached publications of a source record
        :param origin_source_record_uid:
        :return:
        """
        factory = self._get_dao_factory()
        document_created = False
        source_record_dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        document_dao: DocumentDAO = factory.get_dao(Document)
        # get the weakly connected graph of source records that are equivalents (inferred,
        # predicted or asserted) to the source record
        equivalent_source_record_uids = [origin_source_record_uid]
        equivalent_source_record_uids.extend(
            await source_record_dao.get_source_records_equivalent_uids(
                origin_source_record_uid, SourceRecordDAO.EquivalenceType.ALL)
        )
        equivalent_source_record_uids = list(set(equivalent_source_record_uids))
        # for each equivalent source record, fetch the recorded publications and append it to the
        # publications list
        recorded_documents = [
            document
            for source_record_uid in equivalent_source_record_uids
            if (document := await document_dao.get_document_by_source_record_uid(
                source_record_uid)) is not None
        ]
        # Deduplicate recorded_documents by uid
        recorded_documents = list({x.uid: x for x in recorded_documents}.values())
        # case 1 : recorded_documents is empty
        # create a new document
        # and attach all the equivalent source records to it
        # then go to case 2
        if not recorded_documents:
            logger.debug(f"Creating a new document for source record {origin_source_record_uid}")
            document_created = True
            recorded_documents.append(Document(
                source_record_uids=equivalent_source_record_uids))
        # case 2 : recorded_documents contains 1 element
        # attach all the equivalent source records to the existing document
        if len(recorded_documents) == 1:
            document = recorded_documents[0]
            document.source_record_uids = equivalent_source_record_uids
            document.to_be_recomputed = True
            await document_dao.create_or_update_document(
                document=document
            )
        # Case 3: recorded_documents contains multiple elements
        #
        # Elect one document as the main [-> main node election algorithm]
        # For each SourceRecord SRx in equivalent_source_records:
        #    Create (if not already present) an outgoing :RECORDED_BY relationship from
        # main_document to SRX.
        #    Delete outgoing :REPRESENTS relationships to other publications Px where Px ∈ P ≠ P1.
        #    Flag main_document as to_be_recomputed.
        #    Flag other publications Px as to_be_deleted and to be merged into P1.
        elif len(recorded_documents) > 1:
            main_document = self._elect_main_document(recorded_documents)
            for document in recorded_documents:
                if document.uid == main_document.uid:
                    document.source_record_uids = equivalent_source_record_uids
                    document.to_be_recomputed = True
                    document.to_be_deleted = False
                else:
                    # remove all elements of equivalent_source_record_uids
                    # from document.source_record_uids
                    remaining_source_record_uids = [x for x in document.source_record_uids
                                                    if
                                                    x not in equivalent_source_record_uids]
                    document.source_record_uids = remaining_source_record_uids
                    if len(remaining_source_record_uids) == 0:
                        document.to_be_merged_into_uid = main_document.uid
                    else:
                        document.to_be_recomputed = True
                await document_dao.create_or_update_document(
                    document=document
                )
        # Send signal to update the document
        # if the document was created, send the document_created_from_sources signal
        if document_created:
            await document_created_from_sources.send_async(self,
                                                           document_uid=recorded_documents[0].uid)
        else:
            # Otherwise, send the document_sources_changed signal for each recorded document
            for document in recorded_documents:
                await document_sources_changed.send_async(
                    self, document_uid=document.uid, document_created=document_created
                )

    @staticmethod
    def _elect_main_document(documents: list[Document]) -> Document:
        """
        Elect the main document among a list of documents
        :param documents: list of documents
        :return: the main document
        """
        # temporary implementation, the document with the most source records is elected
        # if exaequo, the first one is elected
        return max(documents, key=lambda x: len(x.source_record_uids))

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
