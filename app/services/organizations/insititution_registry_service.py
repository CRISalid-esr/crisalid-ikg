from typing import Optional, List

import aiohttp
from loguru import logger

from app.config import get_app_settings
from app.http.aio_http_client_manager import AioHttpClientManager
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.institution import Institution
from app.models.literal import Literal
from app.models.places import Place
from app.models.structured_physical_address import StructuredPhysicalAddress


class InstitutionRegistryService:
    """
    Service to fetch institution details from the org registry
    """
    def __init__(self):
        settings = get_app_settings()
        self.base_url = settings.org_registry_url

    async def fetch_institution_from_external_source(
            self, identifiers: list[OrganizationIdentifier]
    ) -> Optional[Institution]:
        """
        Fetch institution details from the org registry web service by querying all provided
        OrganizationIdentifierType values in a single request.

        :param identifiers: List of OrganizationIdentifier to search by.
        :return: Institution object if found, otherwise None.
        """
        institution = None
        data = await self._query_external_source(identifiers)
        if data:
            institution = self._hydrate_institution_from_registry_data(data[0])
            # add each provided identifier to the institution if not already present
            for identifier in identifiers:
                if identifier not in institution.identifiers:
                    institution.identifiers.append(identifier)
        return institution

    async def _query_external_source(
            self, identifiers: list[OrganizationIdentifier]
    ) -> List[dict]:
        """
        Fetch institution details from the org registry web service by querying all provided
        OrganizationIdentifierType values in a single request.

        :param identifiers: List of OrganizationIdentifier to search by.
        :return: Institution object if found, otherwise None.
        """
        query_params = ",".join(
            [f"{identifier.type.value.lower()}_id.eq.{identifier.value}" for identifier in
             identifiers]
        )
        query_url = (f"{self.base_url}/organizations?or=({query_params})"
                     "&select=id,name,address,city,postal_code,latitude,longitude,"
                     "country,identifiers,"
                     "metadata->uo_lib_en,metadata->uo_lib_officiel")

        session = await AioHttpClientManager.get_session()
        try:
            async with session.get(query_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        logger.info("Found institution using provided identifiers")
                        return data
                else:
                    logger.warning(
                        f"No institution found for identifiers (status {response.status})"
                    )
        except aiohttp.ClientError as e:
            logger.error(f"Error querying {query_url}: {e}")
            return []

        logger.warning("No institution found from external source.")
        return []

    @classmethod
    def _hydrate_institution_from_registry_data(cls, data: dict) -> Institution:
        """
        Map external API response data to a Pydantic Institution object.
        :param data: Dictionary containing the institution's details.
        :return: Institution object.
        """

        identifiers = cls._build_identifiers_from_registry_data(data)
        names = cls._build_names_from_registry_data(data)
        address = cls._build_addresses_from_registry_data(data)
        place = cls._build_places_from_registry_data(data)

        return Institution(
            names=names,
            identifiers=identifiers,
            addresses=[address],
            places=[place]
        )

    @staticmethod
    def _build_identifiers_from_registry_data(data):
        identifiers = []
        if "uai_id" in data:
            identifiers.append(
                OrganizationIdentifier(type=OrganizationIdentifierType.UAI, value=data["uai_id"]))
        if "identifiers" in data:
            for key, values in data["identifiers"].items():
                for value in values:
                    identifier_type = OrganizationIdentifierType.from_str(key)
                    if identifier_type:
                        identifiers.append(
                            OrganizationIdentifier(type=identifier_type, value=value))
                    else:
                        logger.warning(
                            f"Unknown identifier type : {key} "
                            f"for institution from registry : {data['id']}")
        return identifiers

    @staticmethod
    def _build_places_from_registry_data(data):
        return Place(
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )

    @staticmethod
    def _build_addresses_from_registry_data(data):
        return StructuredPhysicalAddress(
            street=[Literal(value=data["address"], language="fr")] if "address" in data else [],
            city=[Literal(value=data["city"], language="fr")] if "city" in data else [],
            zip_code=[
                Literal(value=data["postal_code"], language="fr")] if "postal_code" in data else [],
            state_or_province=[
                Literal(value=data["reg_nom"], language="fr")] if "reg_nom" in data else [],
            country=[Literal(value=data["country"], language="fr")] if "country" in data else [],
        )

    @staticmethod
    def _build_names_from_registry_data(data):
        names = [
            Literal(value=data["name"], language="fr")
        ]
        if "uo_lib_en" in data:
            names.append(Literal(value=data["uo_lib_en"], language="en"))
        if "uo_lib_officiel" in data:
            names.append(Literal(value=data["uo_lib_officiel"], language="fr"))
        return names
