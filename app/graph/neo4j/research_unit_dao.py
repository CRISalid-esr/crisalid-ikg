from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.research_unit import ResearchUnit
from app.services.identifiers.identifier_service import AgentIdentifierService


class ResearchUnitDAO(Neo4jDAO):
    """
    Data access object for research structures and the neo4j database
    """

    @handle_database_errors
    async def create(self, research_unit: ResearchUnit) -> ResearchUnit:
        """
        Create a research_unit in the graph database

        :param research_unit: research_unit object
        :return: None
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_research_unit_transaction,
                                                research_unit)
        return research_unit

    @handle_database_errors
    async def update(self, research_unit: ResearchUnit) -> ResearchUnit:
        """
        Update a research_unit in the graph database

        :param research_unit: research_unit object
        :return: None
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._update_research_unit_transaction,
                                                research_unit)
        return research_unit

    @handle_database_errors
    async def create_or_update(self, research_unit: ResearchUnit) -> tuple[
        str, Neo4jDAO.Status]:
        """
        Create or update a research_unit in the graph database

        :param research_unit: research_unit object
        :return: the uid of the research_unit and the status of the operation
        """
        status: Neo4jDAO.Status = None
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                local_identifier_value = research_unit.get_identifier(
                    OrganizationIdentifierType.LOCAL).value
                existing_research_unit = await self.find_by_identifier(
                    OrganizationIdentifierType.LOCAL,
                    local_identifier_value
                )
                if existing_research_unit:
                    await session.write_transaction(self._update_research_unit_transaction,
                                                    research_unit)
                    status = self.Status.CREATED
                else:
                    await session.write_transaction(self._create_research_unit_transaction,
                                                    research_unit)
                    status = self.Status.UPDATED
        return research_unit.uid, status

    @handle_database_errors
    async def find_by_identifier(self, identifier_type: OrganizationIdentifierType,
                                 identifier_value: str) -> ResearchUnit | None:
        """
        Find a research_unit by an identifier

        :param identifier_type: identifier type
        :param identifier_value: identifier value
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_research_unit_by_identifier"),
                        identifier_type=identifier_type.value,
                        identifier_value=identifier_value
                    )
                    record = await result.single()
                    if record:
                        return await self._hydrate(record)
                    return None

    @handle_database_errors
    async def get(self, research_unit_uid: str) -> ResearchUnit | None:
        """
        Get a research_unit by its uid

        :param research_unit_uid: research_unit uid
        :return: research_unit object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                return await session.read_transaction(self._get_research_unit_by_uid,
                                                      research_unit_uid)

    @handle_database_errors
    async def get_all_uids(self) -> list[str]:
        """
        Fetch all UIDs of research structures from the database.

        :return: A list of all research structure UIDs.
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(load_query("get_all_research_unit_uids"))
                    return [record["uid"] async for record in result]

    @classmethod
    async def _get_research_unit_by_uid(cls, tx: AsyncSession, research_unit_uid: str):
        result = await tx.run(
            load_query("find_research_unit_by_uid"),
            research_unit_uid=research_unit_uid
        )
        record = await result.single()
        if record:
            return await cls._hydrate(record)
        return None

    @classmethod
    async def _create_research_unit_transaction(cls, tx: AsyncSession,
                                                     research_unit: ResearchUnit):
        research_unit.uid = AgentIdentifierService.compute_uid_for(
            research_unit)
        if not research_unit.uid:
            raise ValueError(
                "The submitted research_unit data is missing a required identifier")
        research_unit_exists = await cls._research_unit_exists(
            research_unit, tx)

        if research_unit_exists is not None:
            raise ConflictError(
                f"Research structure with uid {research_unit.uid} already exists")
        create_research_unit_query = load_query("create_research_unit")
        await tx.run(
            create_research_unit_query,
            research_unit_uid=research_unit.uid,
            acronym=research_unit.acronym,
            names=[name.model_dump() for name in research_unit.names],
            identifiers=[identifier.dict() for identifier in research_unit.identifiers],
            descriptions=[description.model_dump() for description in
                          research_unit.descriptions],
        )
        return research_unit

    @staticmethod
    async def _research_unit_exists(research_unit, tx):
        find_research_unit_query = load_query("research_unit_exists")
        result = await tx.run(find_research_unit_query,
                              research_unit_uid=research_unit.uid)
        record = await result.single()
        return record

    @classmethod
    async def _update_research_unit_transaction(cls, tx: AsyncSession,
                                                     research_unit: ResearchUnit):
        research_unit.uid = research_unit.uid or \
                                 AgentIdentifierService.compute_uid_for(
                                     research_unit
                                 )
        if not research_unit.uid:
            raise ValueError("The submitted research_unit data "
                             "is missing a required identifier")
        research_unit_exists = await cls._research_unit_exists(
            research_unit,
            tx
        )

        if research_unit_exists is None:
            raise NotFoundError("Research structure with uid "
                                f"{research_unit.uid} does not exist")

        delete_names_query = load_query("delete_research_unit_names")
        await tx.run(delete_names_query, research_unit_uid=research_unit.uid)

        create_names_query = load_query("create_research_unit_names")
        await tx.run(
            create_names_query,
            research_unit_uid=research_unit.uid,
            names=[name.dict() for name in research_unit.names]
        )

        # Delete identifiers that are not in the new set
        delete_identifiers_query = load_query("delete_research_unit_identifiers")
        identifier_types = [identifier.type.value for identifier in research_unit.identifiers]
        identifier_values = [identifier.value for identifier in research_unit.identifiers]
        await tx.run(
            delete_identifiers_query,
            research_unit_uid=research_unit.uid,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )

        create_identifiers_query = load_query("create_research_unit_identifiers")
        await tx.run(
            create_identifiers_query,
            research_unit_uid=research_unit.uid,
            identifiers=[identifier.dict() for identifier in research_unit.identifiers]
        )

    @staticmethod
    async def _hydrate(record) -> ResearchUnit:
        research_unit_data = record["s"]
        names_data = record["names"]
        identifiers_data = record["identifiers"]
        descriptions_data = record["descriptions"]
        names = [Literal(**name) for name in names_data]
        identifiers = [OrganizationIdentifier(**identifier)
                       for identifier in identifiers_data]
        research_unit = ResearchUnit(
            uid=research_unit_data["uid"],
            identifiers=identifiers,
            names=names,
            acronym=research_unit_data["acronym"],
            descriptions=[Literal(**description)
                          for description in descriptions_data]
        )
        return research_unit
