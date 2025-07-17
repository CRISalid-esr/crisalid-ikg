from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.institution import Institution
from app.models.literal import Literal
from app.services.identifiers.identifier_service import AgentIdentifierService


class InstitutionDAO(Neo4jDAO):
    """
    Data access object for research structures and the neo4j database
    """

    @handle_database_errors
    async def create(self, institution: Institution) -> Institution:
        """
        Create an institution in the graph database

        :param institution: institution object
        :return: None
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_institution_transaction,
                                                institution)
        return institution

    @handle_database_errors
    async def update(self, institution: Institution) -> Institution:
        """
        Update an institution in the graph database

        :param institution: institution object
        :return: None
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._update_institution_transaction,
                                                institution)
        return institution

    @handle_database_errors
    async def create_or_update(self, institution: Institution) -> tuple[
        str, Neo4jDAO.Status]:
        """
        Create or update an institution in the graph database

        :param institution: institution object
        :return: the uid of the institution and the status of the operation
        """
        status: Neo4jDAO.Status | None = None
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                existing_uid = await session.read_transaction(self._institution_uid, institution)
                if existing_uid is not None:
                    await session.write_transaction(self._update_institution_transaction,
                                                    institution)
                    status = self.Status.CREATED
                else:
                    await session.write_transaction(self._create_institution_transaction,
                                                    institution)
                    status = self.Status.UPDATED
        return institution.uid, status

    @handle_database_errors
    async def find_by_identifiers(
            self, identifiers: list[OrganizationIdentifier]
    ) -> Institution | None:
        """
        Find an institution by any of its identifiers

        :param identifiers: list of identifiers
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    find_institution_query = load_query("find_institution_by_identifiers")
                    result = await tx.run(
                        find_institution_query,
                        identifiers=[{"type": identifier.type.value, "value": identifier.value} for
                                     identifier
                                     in identifiers]
                    )
                    institution = await result.single()
                    if institution:
                        return await self._hydrate(institution)
                    return None

    @handle_database_errors
    async def get(self, institution_uid: str) -> Institution | None:
        """
        Get an institution by its uid

        :param institution_uid: institution uid
        :return: institution object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                return await session.read_transaction(self._get_institution_by_uid,
                                                      institution_uid)

    @classmethod
    async def _create_institution_transaction(cls, tx: AsyncSession,
                                              institution: Institution):
        institution_uid = await cls._institution_uid(tx, institution)

        if institution_uid is not None:
            raise ConflictError(
                f"Institution with the same identifiers already exists: {institution_uid}")
        possible_uids = AgentIdentifierService.compute_possible_uids_for(
            institution)
        institution.uid = possible_uids[0]

        addresses = None
        if institution.addresses:
            addresses = []
            for address in institution.addresses:
                address_dict = {
                    "uid": address.uid,
                    "street": [{"value": s.value, "language": s.language} for s in address.street
                               if s.value] or None,
                    "city": [{"value": c.value, "language": c.language} for c in address.city if
                             c.value] or None,
                    "zip_code": [{"value": z.value, "language": z.language} for z in
                                 address.zip_code if z.value] or None,
                    "state_or_province": [{"value": s.value, "language": s.language} for s in
                                          address.state_or_province if s.value] or None,
                    "country": [{"value": c.value, "language": c.language} for c in
                                address.country if c.value] or None
                }
                addresses.append(address_dict)
        await tx.run(
            load_query("create_institution"),
            uid=institution.uid
        )
        await tx.run(
            load_query("update_institution_names"),
            uid=institution.uid,
            names=[
                {"value": name.value, "language": name.language}
                for name in institution.names if name.value
            ] if institution.names else None
        )
        await tx.run(
            load_query("update_institution_identifiers"),
            uid=institution.uid,
            identifiers=[
                {"type": identifier.type.value, "value": identifier.value}
                for identifier in institution.identifiers if identifier.value
            ] if institution.identifiers else None
        )
        await tx.run(
            load_query("update_institution_addresses"),
            uid=institution.uid,
            addresses=addresses
        )
        await tx.run(
            load_query("update_institution_places"),
            uid=institution.uid,
            places=[
                {"latitude": place.latitude, "longitude": place.longitude}
                for place in institution.places
                if place.latitude is not None and place.longitude is not None
                # ✅ Ensure lat/lon are valid
            ] if institution.places else None
        )

        return institution

    @classmethod
    async def _get_institution_by_uid(cls, tx: AsyncSession, uid: str) -> Institution | None:
        result = await tx.run(
            load_query("find_institution_by_uid"),
            institution_uid=uid
        )
        record = await result.single()
        if record:
            return await cls._hydrate(record)
        return None

    async def institution_uid(self, institution: Institution) -> str | None:
        """
        Check if an institution exists in the database by computing its possible UIDs
        :param institution:
        :return: The uid of the institution if exists, None else
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                return await session.read_transaction(self._institution_uid, institution)

    @staticmethod
    async def _institution_uid(tx: AsyncSession, institution: Institution) -> str | None:
        """
        Check if an institution exists in the database by computing its possible UIDs
        :param institution:
        :param tx:
        :return: The uid of the institution if exists, None else
        """
        possible_uids = AgentIdentifierService.compute_possible_uids_for(
            institution)
        if not possible_uids:
            raise ValueError(
                "The submitted institution data is missing a required identifier")
        find_institution_by_uids_query = load_query("institution_exists_by_uids")
        result = await tx.run(find_institution_by_uids_query,
                              possible_uids=possible_uids)
        record = await result.single()
        return record['s']['uid'] if record else None

    @classmethod
    async def _update_institution_transaction(cls, tx: AsyncSession,
                                              institution: Institution):
        institution_uid = await cls._institution_uid(tx, institution)
        if institution_uid is None:
            raise NotFoundError(
                f"Institution with identifiers {institution.identifiers} not found")
        raise NotImplementedError("Update institution transaction not implemented")

    @classmethod
    async def _hydrate(cls, record) -> Institution:
        institution_data = record["s"]
        names_data = record["names"]
        identifiers_data = record["identifiers"]
        names = [Literal(**name) for name in names_data]
        identifiers = [OrganizationIdentifier(**identifier)
                       for identifier in identifiers_data]
        institution = Institution(
            uid=institution_data["uid"],
            identifiers=identifiers,
            names=names,
        )
        return institution
