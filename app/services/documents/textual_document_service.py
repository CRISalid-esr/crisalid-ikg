from typing import List

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.source_records import SourceRecord


class TextualDocumentService:
    """
    Service to handle operations on publication data
    """
    def __init__(self):
        settings = get_app_settings()
        self.policies = settings.publication_source_policies

    async def recompute_metadata(self, publication_uid : str):
        """
        Recompute metadata for a publication
        :param publication_uid: publication uid
        :return:
        """
        # get source records for the publication
        source_records = await self.get_publication_sources(publication_uid)
        source_records


    async def get_publication_sources(self, publication_uid: str) -> List[SourceRecord]:
        """
        Get a source record from the graph database
        :param source_record_uid: source record uid
        :return: Pydantic SourceRecord object
        """
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        return await dao.get_source_records_by_textual_document_uid(publication_uid)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
