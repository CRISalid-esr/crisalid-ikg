from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.research_structure_dao import ResearchStructureDAO
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure
from app.signals import structure_created, structure_updated


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
        structure = await self._get_research_structure_dao().create(structure)
        structure_created.send_async(self, payload=structure.uid)
        return structure

    async def update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Update a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        structure = await self._get_research_structure_dao().update(structure)
        structure_updated.send_async(self, payload=structure.uid)
        return structure

    async def create_or_update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure if not exists, update otherwise
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        uid, status = await self._get_research_structure_dao().create_or_update(structure)
        if status == DAO.Status.CREATED:
            structure_created.send_async(self, payload=uid)
        elif status == DAO.Status.UPDATED:
            structure_updated.send_async(self, payload=uid)
        return structure

    async def get_structure_by_identifier(self,
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
        return await (self._get_research_structure_dao()
                      .find_by_identifier(identifier_type, identifier_value))

    async def get_structure_by_uid(self, uid: str) -> ResearchStructure:
        """
        Get a structure from the graph database
        :param uid: Researched structure uid
        :return: Pydantic ResearchStructure object
        """
        return await self._get_research_structure_dao().get(uid)

    @staticmethod
    def _get_research_structure_dao() -> ResearchStructureDAO:
        settings = get_app_settings()
        return cast(
            ResearchStructureDAO,
            AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(ResearchStructure)
        )
