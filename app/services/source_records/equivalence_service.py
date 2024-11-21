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
        await self._update_equivalents()

    async def _update_equivalents(self) -> None:
        """
        Update the equivalent source records
        :return:
        """

        # pop the first element of source_records_to_update; if empty, abort
        if not self.source_records_to_update:
            return
        source_record_id = self.source_records_to_update.pop(0)

        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        new_inferred_equivalents = await dao.get_inferred_equivalents(source_record_id)
        await self._update_equivalents()


    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
