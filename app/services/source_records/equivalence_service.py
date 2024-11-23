from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord

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
        print(f"beginning to update source record with id {source_record_id}")
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
        origin_source_record_uid = self.source_records_to_update_uids.pop(0)
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        # Fetch the weakly connected graph of source records that share identifiers with the origin
        sr_with_shared_identifier_uids = [origin_source_record_uid]
        sr_with_shared_identifier_uids.extend(
            await (
                dao.get_source_records_with_shared_identifier_uids(
                    origin_source_record_uid)
            ))
        sr_with_shared_identifier_uids = list(set(sr_with_shared_identifier_uids))
        # Fetch the weakly connected graph of source records that are inferred to be equivalent to
        # one of the source records in the weakly connected graph of shared identifiers
        existing_inferred_equiv_sr_uids = [origin_source_record_uid]
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
        for origin_source_record_uid in obsolete_inferred_equiv_sr_uids:
            await dao.delete_inferred_equivalence_relationships(origin_source_record_uid,
                                                                sr_with_shared_identifier_uids)
            # Add any detached source records to the list of records to update
            self.source_records_to_update_uids.append(origin_source_record_uid)
        await dao.create_inferred_equivalence_relationships(
            sr_with_shared_identifier_uids)
        # Handle attached publications
        await self._update_attached_publications(origin_source_record_uid)
        # Loop until the source_records_to_update list is empty
        await self._update_inferred_equivalence_relationships()

    async def _update_attached_publications(self, origin_source_record_uid) -> None:
        """
        Update the attached publications of a source record
        :param origin_source_record_uid:
        :return:
        """
        factory = self._get_dao_factory()
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
        recorded_textual_documents = [
            document
            for source_record_uid in equivalent_source_record_uids
            if (document := await document_dao.get_textual_document_by_source_record_uid(
                source_record_uid)) is not None
        ]
        # case 1 : recorded_textual_documents is empty
        # create a new textual document
        # and attach all the equivalent source records to it
        if not recorded_textual_documents:
            new_textual_document = await document_dao.create_textual_document_from_source_records(
                source_record_uids=equivalent_source_record_uids
            )
            recorded_textual_documents.append(new_textual_document)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
