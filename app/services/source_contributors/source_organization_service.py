from __future__ import annotations

from typing import List

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.source_organizations import SourceOrganization


class SourceOrganizationService:
    """
    Service to handle operations on source organizations data (source layer only).
    """

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)

    async def create_or_update_source_organization(
            self,
            source_organization: SourceOrganization) -> SourceOrganization:
        """
        Create or update a SourceOrganization in the graph database from a Pydantic
        SourceOrganization object.
        :param source_organization: Pydantic SourceOrganization object
        :return:
        """
        factory = self._get_dao_factory()
        dao: SourceOrganizationDAO = factory.get_dao(SourceOrganization)

        assert source_organization.uid, (
            "Source organization uid should have been computed before from "
            f"{source_organization.source} and {source_organization.source_identifier}"
        )

        if await dao.source_organization_exists(source_organization.uid):
            return await dao.update(source_organization)
        return await dao.create(source_organization)

    async def get_source_organization_by_uid(self, uid: str) -> SourceOrganization:
        """
        Retrieve a SourceOrganization by its UID.
        """
        factory = self._get_dao_factory()
        dao: SourceOrganizationDAO = factory.get_dao(SourceOrganization)
        return await dao.get_by_uid(uid)

    async def get_cluster(self, source_organization_uid: str) -> List[SourceOrganization]:
        """
        Returns the transitive cluster of SourceOrganizations connected by identifiers.
        """
        factory = self._get_dao_factory()
        dao: SourceOrganizationDAO = factory.get_dao(SourceOrganization)
        return await dao.create_source_organization_cluster(source_organization_uid)
