from __future__ import annotations

from loguru import logger

from app.config import get_app_settings
from app.errors.database_error import DatabaseError
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
        Compute the location of an AuthorityOrganizationState from its source organizations
        :param state_uid:
        :return:
        """
        auth_org_dao = self._get_authority_org_dao()
        state = await auth_org_dao.get_authority_organization_state_by_uid(state_uid)

        source_org_dao = self._get_source_org_dao()
        source_orgs = [await source_org_dao.get_by_uid(uid) for uid
                       in state.source_organization_uids]

        address_list = []
        place_list = []

        ror_identifier = next((id for source_org in source_orgs
             for id in source_org.identifiers if id.type == "ror" ), None)

        if ror_identifier and ror_identifier.extra_information:
            geoinformations = ror_identifier.extra_information.get("geonames_locations")
            for geolocation in geoinformations:
                latitude = geolocation.get("lat", None)
                longitude = geolocation.get("lng", None)
                if latitude and longitude:
                    place_list.append(Place(latitude=latitude,longitude=longitude))

                address = StructuredPhysicalAddress(
                    street=[Literal(value=geolocation["street"].strip(), language="fr")]
                        if "street" in geolocation else [],
                    city=[Literal(value=geolocation["name"].strip(), language="fr")]
                        if "name" in geolocation else [],
                    zip_code=[Literal(value=geolocation["zip_code"].strip(), language="fr")]
                        if "zip_code" in geolocation else [],
                    state_or_province=[
                        Literal(value=geolocation["country_subdivision_name"].strip(),
                                language="fr")]
                            if "country_subdivision_name" in geolocation else [],
                    country=[Literal(value=geolocation["country_name"].strip(),
                                     language="fr")]
                        if "country_name" in geolocation else [],
                    continent=[Literal(value=geolocation["continent_name"].strip(),
                                       language="fr")]
                        if "continent_name" in geolocation else [],
                )
                address_list.append(address)

        try:
            await auth_org_dao.attach_place_and_address_nodes_to_state(state_uid,
                                                                   place_list,
                                                                   address_list)

        except DatabaseError as e:
            logger.error(f"Error attaching place and address to "
                         f"AuthorityOrganizationState {state_uid}: {e}")

        return

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
        return factory.get_dao(AuthorityOrganizationState)

    def _get_source_org_dao(self) -> SourceOrganizationDAO:
        factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
        return factory.get_dao(SourceOrganization)
