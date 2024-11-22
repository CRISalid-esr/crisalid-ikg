from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.source_records import SourceRecord


class EquivalenceService:
    """
    Service to handle equivalence relationships between source records
    """

    def __init__(self):
        self.source_records_to_update = []

    async def update_source_record(self, _, source_record_id) -> None:
        """
        Update a source record with the given id
        :param _:
        :param source_record_id:
        :return:
        """
        print(f"beginning to update source record with id {source_record_id}")
        self.source_records_to_update.append(source_record_id)
        await self._update_inferred_equivalence_relationships()

    async def _update_inferred_equivalence_relationships(self) -> None:
        """
        Update the equivalent source records
        :return:
        """
        if not self.source_records_to_update:
            return
        source_record_uid = self.source_records_to_update.pop(0)
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        sr_with_shared_identifier_uids = self._gather(
            source_record_uid,
            await (
                dao.get_source_records_with_shared_identifier_uids(
                    source_record_uid)
            ))
        existing_inferred_equiv_sr_uids = self._gather(
            source_record_uid,
            await dao.get_source_records_inferred_equivalent_uids(
                source_record_uid))
        obsolete_inferred_equiv_sr_uids = [x for x in existing_inferred_equiv_sr_uids if
                                           x not in sr_with_shared_identifier_uids]
        for source_record_uid in obsolete_inferred_equiv_sr_uids:
            await dao.delete_inferred_equivalence_relationships(source_record_uid,
                                                                sr_with_shared_identifier_uids)
            self.source_records_to_update.append(source_record_uid)
        await dao.create_inferred_equivalence_relationships(
            sr_with_shared_identifier_uids)

        await self._update_inferred_equivalence_relationships()

    def _gather(self, source_record_uid, other_uids):
        return list(
            set(other_uids + [source_record_uid]))

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
