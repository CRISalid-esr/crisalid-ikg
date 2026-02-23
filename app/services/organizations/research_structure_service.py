from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.research_structure_dao import ResearchStructureDAO
from app.models.identifier_types import OrganizationIdentifierType
from app.models.research_structures import ResearchStructure
from app.signals import structure_created, structure_updated, structure_unchanged, structure_deleted


class ResearchStructureService:
    """
    Service to handle operations on structure data
    """

    async def signal_research_unit_created(self, uid: str):
        """
        Dispatch the 'created' signal for a research structure.
        :param uid: The UID of the structure
        """
        await structure_created.send_async(self, payload=uid)

    async def signal_research_unit_updated(self, uid: str):
        """
        Dispatch the 'updated' signal for a research structure.
        :param uid: The UID of the structure
        """
        await structure_updated.send_async(self, payload=uid)

    async def signal_research_unit_unchanged(self, uid: str):
        """
        Simulate a signal for an unchanged research structure.
        :param uid: The UID of the structure
        """
        await structure_unchanged.send_async(self, payload=uid)

    async def signal_research_unit_deleted(self, uid: str):
        """
        Dispatch the 'deleted' signal for a research structure.
        :param uid: The UID of the structure
        """
        await structure_deleted.send_async(self, payload=uid)

    async def create_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        structure = await self._get_research_structure_dao().create(structure)
        await self.signal_research_unit_created(structure.uid)
        return structure

    async def update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Update a structure in the graph database from a Pydantic ResearchStructure object
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        structure = await self._get_research_structure_dao().update(structure)
        await self.signal_research_unit_updated(structure.uid)
        return structure

    async def create_or_update_structure(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure if not exists, update otherwise
        :param structure: Pydantic ResearchStructure object
        :return:
        """
        uid, status = await self._get_research_structure_dao().create_or_update(structure)
        if status == DAO.Status.CREATED:
            await self.signal_research_unit_created(uid)
        elif status == DAO.Status.UPDATED:
            await self.signal_research_unit_updated(uid)
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

    async def get_all_structure_uids(self) -> list[str]:
        """
        Retrieve all research structure UIDs from the database.

        :return: A list of all research structure UIDs.
        """
        dao = self._get_research_structure_dao()
        return await dao.get_all_uids()

    @staticmethod
    def _get_research_structure_dao() -> ResearchStructureDAO:
        settings = get_app_settings()
        return cast(
            ResearchStructureDAO,
            AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(ResearchStructure)
        )
