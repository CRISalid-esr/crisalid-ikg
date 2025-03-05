from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.institution_dao import InstitutionDAO
from app.models.institution import Institution
from app.services.organizations.insititution_registry_service import InstitutionRegistryService
from app.signals import institution_created, institution_updated, institution_unchanged, \
    institution_deleted


class InstitutionService:
    """
    Service to handle operations on institutions in the graph database.
    """

    async def signal_institution_created(self, uid: str):
        """
        Dispatch the 'created' signal for an institution.
        :param uid: The UID of the institution
        """
        await institution_created.send_async(self, payload=uid)

    async def signal_institution_updated(self, uid: str):
        """
        Dispatch the 'updated' signal for an institution.
        :param uid: The UID of the institution
        """
        await institution_updated.send_async(self, payload=uid)

    async def signal_institution_unchanged(self, uid: str):
        """
        Simulate a signal for an unchanged institution.
        :param uid: The UID of the institution
        """
        await institution_unchanged.send_async(self, payload=uid)

    async def signal_institution_deleted(self, uid: str):
        """
        Dispatch the 'deleted' signal for an institution.
        :param uid: The UID of the institution
        """
        await institution_deleted.send_async(self, payload=uid)

    async def create_institution(self, institution: Institution) -> Institution:
        """
        Create an institution in the graph database from a Pydantic Institution object
        :param institution: Pydantic Institution object
        :return:
        """
        institution_registry_service = InstitutionRegistryService()
        institution_from_external_source = \
            await institution_registry_service.fetch_institution_from_external_source(
                institution.identifiers
            )
        if institution_from_external_source is None:
            raise ValueError(
                f"No institution found from external source for {institution.identifiers}"
            )
        institution = await self._get_institution_dao().create(institution_from_external_source)
        await self.signal_institution_created(institution.uid)
        return institution

    async def update_institution(self, institution: Institution) -> Institution:
        """
        Update an institution in the graph database from a Pydantic Institution object
        :param institution: Pydantic Institution object
        :return:
        """
        institution = await self._get_institution_dao().update(institution)
        await self.signal_institution_updated(institution.uid)
        return institution

    async def create_or_update_institution(self, institution: Institution) -> Institution:
        """
        Create an institution if not exists, update otherwise
        :param institution: Pydantic Institution object
        :return:
        """
        uid, status = await self._get_institution_dao().create_or_update(institution)
        if status == DAO.Status.CREATED:
            await self.signal_institution_created(uid)
        elif status == DAO.Status.UPDATED:
            await self.signal_institution_updated(uid)
        return institution

    async def institution_uid(self,
                              institution: Institution) -> str | None:
        """
        Check if an institution exists in the graph database and return its uis
        :param institution: Pydantic Institution object
        :return: The uid of the institution if exists, None else
        """
        return await (self._get_institution_dao().institution_uid(institution))

    async def get_institution_by_uid(self, uid: str) -> Institution:
        """
        Get an institution from the graph database
        :param uid: Researched institution uid
        :return: Pydantic Institution object
        """
        return await self._get_institution_dao().get(uid)

    @staticmethod
    def _get_institution_dao() -> InstitutionDAO:
        settings = get_app_settings()
        return cast(
            InstitutionDAO,
            AbstractDAOFactory().get_dao_factory(settings.graph_db).get_dao(Institution)
        )
