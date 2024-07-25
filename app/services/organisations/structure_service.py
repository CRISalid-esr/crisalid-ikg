from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.structure_dao import StructureDAO
from app.models.research_structures import ResearchStructure


class StructureService:
    """
    Service to handle operations on structure data
    """

    async def create_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        factory = self._get_structure_dao()
        dao: StructureDAO = factory.get_dao(ResearchStructure)
        return await dao.create(structure)

    async def update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Update a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        factory = self._get_structure_dao()
        dao: StructureDAO = factory.get_dao(ResearchStructure)
        return await dao.update(structure)

    async def create_or_update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure if not exists, update otherwise
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        factory = self._get_structure_dao()
        dao: StructureDAO = factory.get_dao(ResearchStructure)
        return await dao.create_or_update(structure)

    @staticmethod
    def _get_structure_dao() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
