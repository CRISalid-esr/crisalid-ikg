from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.models.research_structures import ResearchStructure


class ResearchStructureService:
    """
    Service to handle operations on structure data
    """

    @staticmethod
    async def compute_research_structure_id(research_structure: ResearchStructure) -> str:
        """
        Compute the structure id from the structure identifiers
        The selected identifier is the first one found among the identifiers
        in the order defined in the settings
        :param research_structure:
        :return:
        """
        settings = get_app_settings()
        identifier_order = settings.structure_identifier_order
        structure_id = None
        for identifier_type in identifier_order:
            if identifier_type in [identifier.type for identifier in
                                   research_structure.identifiers]:
                selected_identifier = next(
                    identifier for identifier in research_structure.identifiers
                    if identifier.type == identifier_type
                )
                structure_id = f"{selected_identifier.type.value}-{selected_identifier.value}"
                break
        return structure_id

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

    @staticmethod
    def _get_structure_dao() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
