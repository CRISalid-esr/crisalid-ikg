from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.research_structures import ResearchStructure
from app.services.organizations.research_structure_service import ResearchStructureService


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

    @staticmethod
    async def _create_research_structure_transaction(tx: AsyncSession,
                                                     research_structure: ResearchStructure):
        research_structure.id = await ResearchStructureService.compute_research_structure_id(
            research_structure)
        if not research_structure.id:
            raise ValueError(
                "The submitted research_structure data is missing a required identifier")
        existing_research_structure = await ResearchStructureDAO._find_research_structure_by_id(
            research_structure, tx)

        if existing_research_structure is not None:
            raise ConflictError(
                f"Research structure with id {research_structure.id} already exists")

        create_research_structure_query = """
                    CREATE (research_struct:Organisation:ResearchStructure {id: $research_structure_id})
                    WITH research_struct
                    UNWIND $names AS name
                    WITH research_struct, name
                    CREATE (rs_name:Literal {value: name.value, language: name.language})
                    CREATE (research_struct)-[:HAS_NAME]->(rs_name)
                    WITH research_struct
                    UNWIND $identifiers AS identifier
                    CREATE (rs_identifier:AgentIdentifier {type: identifier.type, value: identifier.value})
                    CREATE (research_struct)-[:HAS_IDENTIFIER]->(rs_identifier)
                """
        await tx.run(
            create_research_structure_query,
            research_structure_id=research_structure.id,
            names=[name.dict() for name in research_structure.names],
            identifiers=[identifier.dict() for identifier in research_structure.identifiers]
        )
        return research_structure

    @staticmethod
    async def _find_research_structure_by_id(research_structure, tx):
        find_research_structure_query = """
                MATCH (s:ResearchStructure {id: $research_structure_id})
                RETURN s
                """
        result = await tx.run(find_research_structure_query,
                              research_structure_id=research_structure.id)
        record = await result.single()
        return record

    @staticmethod
    async def _update_research_structure_transaction(tx: AsyncSession,
                                                     research_structure: ResearchStructure):
        if research_structure.id is None:
            research_structure.id = await ResearchStructureService.compute_research_structure_id(
                research_structure
            )
        if not research_structure.id:
            raise ValueError("The submitted research_structure data "
                             "is missing a required identifier")
        existing_research_structure = await ResearchStructureDAO._find_research_structure_by_id(
            research_structure,
            tx
        )

        if existing_research_structure is None:
            raise NotFoundError("Research structure with id "
                                f"{research_structure.id} does not exist")

        # Delete existing names
        delete_names_query = """
                MATCH (s:ResearchStructure {id: $research_structure_id})-[:HAS_NAME]->(n:OrganizationName)
                DETACH DELETE n
            """
        await tx.run(delete_names_query, research_structure_id=research_structure.id)

        # Create new names with literals
        create_names_query = """
                MATCH (s:ResearchStructure {id: $research_structure_id})
                UNWIND $names AS name
                CREATE (sn:OrganizationName)
                WITH s, sn, name
                UNWIND name.first_names AS first_name
                CREATE (fn:Literal {value: first_name.value, language: first_name.language})
                CREATE (sn)-[:HAS_FIRST_NAME]->(fn)
                WITH s, sn, name
                UNWIND name.last_names AS last_name
                CREATE (ln:Literal {value: last_name.value, language: last_name.language})
                CREATE (sn)-[:HAS_LAST_NAME]->(ln)
                CREATE (s)-[:HAS_NAME]->(sn)
            """
        await tx.run(
            create_names_query,
            research_structure_id=research_structure.id,
            names=[name.dict() for name in research_structure.names]
        )

        # Delete identifiers that are not in the new set
        delete_identifiers_query = """
                MATCH (s:ResearchStructure {id: $research_structure_id})-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
                WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
                DETACH DELETE i
            """
        identifier_types = [identifier.type.value for identifier in research_structure.identifiers]
        identifier_values = [identifier.value for identifier in research_structure.identifiers]
        await tx.run(
            delete_identifiers_query,
            research_structure_id=research_structure.id,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )

        # Create or update identifiers
        create_identifiers_query = """
                MATCH (s:ResearchStructure {id: $research_structure_id})
                UNWIND $identifiers AS identifier
                MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
                ON CREATE SET i = identifier
                ON MATCH SET i = identifier
                MERGE (s)-[:HAS_IDENTIFIER]->(i)
            """
        await tx.run(
            create_identifiers_query,
            research_structure_id=research_structure.id,
            identifiers=[identifier.dict() for identifier in research_structure.identifiers]
        )

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
                        self._find_by_identifier_query,
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
                            id=research_structure_data["id"],
                            identifiers=identifiers,
                            names=names
                        )

                        return research_structure
                    return None

    _find_by_identifier_query = """
        MATCH (s:ResearchStructure)-[:HAS_NAME]->(n:Literal)
        MATCH (s)-[:HAS_IDENTIFIER]->(i1:AgentIdentifier {type: $identifier_type, value: $identifier_value})
        MATCH (s)-[:HAS_IDENTIFIER]->(i2:AgentIdentifier)
        RETURN s, collect(n) as names, collect(i2) as identifiers
    """
