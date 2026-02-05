from __future__ import annotations

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.authority_organization_dao import AuthorityOrganizationDAO
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.literal import Literal
from app.models.places import Place
from app.models.source_organizations import SourceOrganization
from app.models.structured_physical_address import StructuredPhysicalAddress

class AuthorityOrganizationLocationService:
    """
    Handle location information for AuthorityOrganizations
    """

    async def add_location_from_source_organizations(self, _, state_uid: str):
        """
        Compute location information for an updated AuthorityOrganizationState
        :param _: unused (for compatibility with signal handlers)
        :param state_uid: the AuthorityOrganizationState uid
        :return:
        """
        await self._compute_location_from_source_organization(state_uid)

    async def _compute_location_from_source_organization(self, state_uid) -> bool:
        """
        Compute the location of an AuthorityOrganizationState from its source organizations
        :param document_uid:
        :return: False if the document should be deleted (i.e. has no source records)
        """
        auth_org_dao = self._get_authority_org_dao()
        state = await auth_org_dao.get_authority_organization_state_by_uid(state_uid)

        source_org_dao = self._get_source_org_dao()
        source_orgs = [await source_org_dao.get_by_uid(uid) for uid
                       in state.source_organization_uids]

        address_list = []
        place_list = []
        for source_org in source_orgs:
            for identifier in source_org.identifiers:
                if identifier.type == "ror" and identifier.extra_information:
                    geoinformations = identifier.extra_information.get("geonames_locations")
                    for geolocation in geoinformations:
                        latitude = geolocation.get("lat")
                        longitude = geolocation.get("lng")
                        place_list.append(Place(latitude=latitude,longitude=longitude))

                        address = StructuredPhysicalAddress(
                            street=[Literal(value=geolocation["street"], language="fr")]
                                if "street" in geolocation else [],
                            city=[Literal(value=geolocation["name"], language="fr")]
                                if "name" in geolocation else [],
                            zip_code=[Literal(value=geolocation["zip_code"], language="fr")]
                                if "zip_code" in geolocation else [],
                            state_or_province=[
                                Literal(value=geolocation["country_subdivision_name"],
                                        language="fr")]
                                    if "country_subdivision_name" in geolocation else [],
                            country=[Literal(value=geolocation["country_name"], language="fr")]
                                if "country_name" in geolocation else [],
                            continent=[Literal(value=geolocation["continent_name"], language="fr")]
                                if "continent_name" in geolocation else [],
                        )
                        address_list.append(address)

        await auth_org_dao.attach_place_and_address_nodes_to_state(state_uid,
                                                                   place_list,
                                                                   address_list)
        return True

    async def get_location_from_state(self, state_uid: str):
        """
        Get location information for an AuthorityOrganizationState
        :param _: unused (for compatibility with signal handlers)
        :param state_uid: the AuthorityOrganizationState uid
        :return:
        """
        auth_org_dao = self._get_authority_org_dao()
        addresses, places = await auth_org_dao.get_location_of_state_by_uid(state_uid)
        return addresses, places

    def _get_authority_org_dao(self) -> AuthorityOrganizationDAO:
        factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
        # Your DAO factory likely ignores the model type, but keep consistent with your pattern:
        return factory.get_dao(AuthorityOrganizationState)

    def _get_source_org_dao(self) -> SourceOrganizationDAO:
        factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
        # Your DAO factory likely ignores the model type, but keep consistent with your pattern:
        return factory.get_dao(SourceOrganization)
