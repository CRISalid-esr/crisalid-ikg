from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure


class ResearchStructureService:
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
        dao: DAO = factory.get_dao(ResearchStructure)
        return await dao.create(structure)

    async def update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Update a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        factory = self._get_structure_dao()
        dao: DAO = factory.get_dao(ResearchStructure)
        return await dao.update(structure)

    async def create_or_update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure if not exists, update otherwise
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        factory = self._get_structure_dao()
        dao: DAO = factory.get_dao(ResearchStructure)
        return await dao.create_or_update(structure)

    async def get_structure(self,
                            identifier_value: str,
                            identifier_type: OrganizationIdentifierType =
                            OrganizationIdentifierType.LOCAL,
                            ) -> ResearchStructure:
        """
        Get a structure from the graph database
        :param identifier_value: Researched identifier value
        :param identifier_type: OrgganizationIdentifierType corresponding to the researched value
        :return: Pydantic ResearchStructure object
        """
        factory = self._get_structure_dao()
        dao: DAO = factory.get_dao(ResearchStructure)
        return await dao.find_by_identifier(identifier_type, identifier_value)

    @staticmethod
    def _get_structure_dao() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
