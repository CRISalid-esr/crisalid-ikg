from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.research_structures import ResearchStructure
from app.services.identifiers.identifier_service import AgentIdentifierService
from app.graph.neo4j.utils import load_query

class ResearchStructureDAO(Neo4jDAO):
    """
    Data access object for research structures and the neo4j database
    """

    async def create(self, research_structure: ResearchStructure) -> ResearchStructure:
        """
        Create a research_structure in the graph database

        :param research_structure: research_structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_research_structure_transaction,
                                                research_structure)
        return research_structure

    async def update(self, research_structure: ResearchStructure) -> ResearchStructure:
        """
        Update a research_structure in the graph database

        :param research_structure: research_structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._update_research_structure_transaction,
                                                research_structure)
        return research_structure

    async def create_or_update(self, research_structure: ResearchStructure) -> ResearchStructure:
        """
        Create or update a research_structure in the graph database

        :param research_structure: research_structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                local_identifier_value = research_structure.get_identifier(
                    OrganizationIdentifierType.LOCAL).value
                existing_research_structure = await self.find_by_identifier(
                    OrganizationIdentifierType.LOCAL,
                    local_identifier_value
                )
                if existing_research_structure:
                    await session.write_transaction(self._update_research_structure_transaction,
                                                    research_structure)
                else:
                    await session.write_transaction(self._create_research_structure_transaction,
                                                    research_structure)
        return research_structure

    async def find_by_identifier(self, identifier_type: OrganizationIdentifierType,
                                 identifier_value: str) -> ResearchStructure | None:
        """
        Find a research_structure by an identifier

        :param identifier_type: identifier type
        :param identifier_value: identifier value
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_structure_by_identifier"),
                        identifier_type=identifier_type.value,
                        identifier_value=identifier_value
                    )
                    record = await result.single()
                    if record:
                        research_structure_data = record["s"]
                        names_data = record["names"]
                        identifiers_data = record["identifiers"]

                        names = [Literal(**name) for name in names_data]
                        identifiers = [OrganizationIdentifier(**identifier)
                                       for identifier in identifiers_data]

                        research_structure = ResearchStructure(
                            uid=research_structure_data["uid"],
                            identifiers=identifiers,
                            names=names
                        )

                        return research_structure
                    return None

    @classmethod
    async def _create_research_structure_transaction(cls, tx: AsyncSession,
                                                     research_structure: ResearchStructure):
        research_structure.uid = AgentIdentifierService.compute_uid_for(
            research_structure)
        if not research_structure.uid:
            raise ValueError(
                "The submitted research_structure data is missing a required identifier")
        existing_research_structure = await cls._find_research_structure_by_id(
            research_structure, tx)

        if existing_research_structure is not None:
            raise ConflictError(
                f"Research structure with uid {research_structure.uid} already exists")
        create_research_structure_query = load_query("create_research_structure")
        await tx.run(
            create_research_structure_query,
            research_structure_uid=research_structure.uid,
            names=[name.dict() for name in research_structure.names],
            identifiers=[identifier.dict() for identifier in research_structure.identifiers]
        )
        return research_structure

    @staticmethod
    async def _find_research_structure_by_id(research_structure, tx):
        find_research_structure_query = load_query("find_research_structure")
        result = await tx.run(find_research_structure_query,
                              research_structure_uid=research_structure.uid)
        record = await result.single()
        return record

    @classmethod
    async def _update_research_structure_transaction(cls, tx: AsyncSession,
                                                     research_structure: ResearchStructure):
        research_structure.uid = research_structure.uid or \
                                 AgentIdentifierService.compute_uid_for(
                                     research_structure
                                 )
        if not research_structure.uid:
            raise ValueError("The submitted research_structure data "
                             "is missing a required identifier")
        existing_research_structure = await cls._find_research_structure_by_id(
            research_structure,
            tx
        )

        if existing_research_structure is None:
            raise NotFoundError("Research structure with uid "
                                f"{research_structure.uid} does not exist")

        delete_names_query = load_query("delete_structure_names")
        await tx.run(delete_names_query, research_structure_uid=research_structure.uid)

        create_names_query = load_query("create_structure_names")
        await tx.run(
            create_names_query,
            research_structure_uid=research_structure.uid,
            names=[name.dict() for name in research_structure.names]
        )

        # Delete identifiers that are not in the new set
        delete_identifiers_query = load_query("delete_structure_identifiers")
        identifier_types = [identifier.type.value for identifier in research_structure.identifiers]
        identifier_values = [identifier.value for identifier in research_structure.identifiers]
        await tx.run(
            delete_identifiers_query,
            research_structure_uid=research_structure.uid,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )

        # Create or update identifiers
        create_identifiers_query = load_query("create_structure_identifiers")
        await tx.run(
            create_identifiers_query,
            research_structure_uid=research_structure.uid,
            identifiers=[identifier.dict() for identifier in research_structure.identifiers]
        )
