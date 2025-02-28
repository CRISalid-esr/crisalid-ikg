from typing import cast, Optional

import aiohttp
from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.institution_dao import InstitutionDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.institution import Institution
from app.models.literal import Literal
from app.models.places import Place
from app.models.structured_physical_address import StructuredPhysicalAddress
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
        institution_from_external_source = await self._fetch_institution_from_external_source(
            institution.identifiers
        )
        if institution_from_external_source is None:
            raise ValueError(
                f"No institution found from external source for {institution.identifiers}")
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

    async def _fetch_institution_from_external_source(
            self, identifiers: list[OrganizationIdentifier]
    ) -> Optional[Institution]:
        """
        Fetch institution details from the ORD registry web service by querying all provided
        OrganizationIdentifierType values one by one.

        :param identifiers: List of OrganizationIdentifier to search by.
        :return: Institution object if found, otherwise None.
        """
        settings = get_app_settings()
        base_url = settings.org_registry_url  # Base URL for the external service

        async with aiohttp.ClientSession() as session:
            for identifier in identifiers:
                identifier_key = f"{identifier.type.value.lower()}_id"
                identifier_value = identifier.value
                query_url = f"{base_url}/organizations?{identifier_key}=eq.{identifier_value}"

                try:
                    async with session.get(query_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data:
                                logger.info(
                                    "Found institution using "
                                    f"{identifier.type}: {identifier_value}")
                                return self._hydrate_institution_from_registry_data(
                                    data[0])  # Return first result
                        else:
                            logger.warning(
                                "No institution found for "
                                f"{identifier.type}: {identifier_value} "
                                f"(status {response.status})")
                except aiohttp.ClientError as e:
                    logger.error(f"Error querying {query_url}: {e}")

        logger.info("No institution found from external source.")
        return None

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
                    identifier_type = OrganizationIdentifierType.get_identifier_type_from_str(key)
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
        metadata = data.get("metadata", {})
        if "uo_lib_en" in metadata:
            names.append(Literal(value=metadata["uo_lib_en"], language="en"))
        if "uo_lib_officiel" in metadata:
            names.append(Literal(value=metadata["uo_lib_officiel"], language="fr"))
        return names
