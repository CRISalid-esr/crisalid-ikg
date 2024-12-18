from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.source_organizations import SourceOrganization


class SourceOrganizationService:
    """
    Service to handle operations on source journals data
    """

    async def create_or_update_source_organization(self,
                                                   source_organization: SourceOrganization) -> (
            SourceOrganization):
        """
        Create a source contributor in the graph database from a Pydantic SourceContributor object
        :param source_organization: Pydantic SourceContributor object
        :return:
        """
        factory = self._get_dao_factory()
        source_organization_dao: SourceOrganizationDAO = factory.get_dao(SourceOrganization)
        assert source_organization.uid, \
            "Source organization uid should have been computed before from" \
            f"{source_organization.source} and {source_organization.source_identifier}"
        source_organization_exists = await source_organization_dao.source_organization_exists(
            source_organization.uid)
        if source_organization_exists:
            return await source_organization_dao.update(source_organization)
        return await source_organization_dao.create(source_organization)

    async def get_source_organization_by_uid(self, uid: str) -> SourceOrganization:
        """
        Get a source organization from the graph database by its uid
        :param uid: source organization uid
        :return: source organization object
        """
        factory = self._get_dao_factory()
        source_organization_dao: SourceOrganizationDAO = factory.get_dao(SourceOrganization)
        return await source_organization_dao.get_by_uid(uid)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
