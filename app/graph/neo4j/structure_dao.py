from neo4j import AsyncSession

from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.research_structures import ResearchStructure
from app.services.organisations.structure_service import StructureService


class StructureDAO(Neo4jDAO):
    """
    Data access object for structures and the neo4j database
    """

    async def create(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create a structure in the graph database

        :param structure: structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_structure_transaction, structure)
        return structure

    async def update(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Update a structure in the graph database

        :param structure: structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._update_structure_transaction, structure)
        return structure

    async def create_or_update(self, structure: ResearchStructure) -> ResearchStructure:
        """
        Create or update a structure in the graph database

        :param structure: structure object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                local_identifier_value = structure.get_identifier(
                    OrganizationIdentifierType.LOCAL).value
                existing_structure = await self.find_by_identifier(
                    OrganizationIdentifierType.LOCAL,
                    local_identifier_value
                )
                if existing_structure:
                    await session.write_transaction(self._update_structure_transaction, structure)
                else:
                    await session.write_transaction(self._create_structure_transaction, structure)
        return structure

    @staticmethod
    async def _create_structure_transaction(tx: AsyncSession, structure: ResearchStructure):
        structure.id = await StructureService.compute_structure_id(structure)
        if not structure.id:
            raise ValueError("The submitted structure data is missing a required identifier")
        existing_structure = await StructureDAO._find_structure_by_id(structure, tx)

        if existing_structure is not None:
            raise ConflictError(f"Structure with id {structure.id} already exists")

        create_structure_query = """
                    CREATE (research_struct:Organisation:ResearchStructure {id: $structure_id})
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
            create_structure_query,
            structure_id=structure.id,
            names=[name.dict() for name in structure.names],
            identifiers=[identifier.dict() for identifier in structure.identifiers]
        )
        return structure

    @staticmethod
    async def _find_structure_by_id(structure, tx):
        find_structure_query = """
                MATCH (s:ResearchStructure {id: $structure_id})
                RETURN s
                """
        result = await tx.run(find_structure_query, structure_id=structure.id)
        record = await result.single()
        return record

    @staticmethod
    async def _update_structure_transaction(tx: AsyncSession, structure: ResearchStructure):
        if structure.id is None:
            structure.id = await StructureService.compute_structure_id(structure)
        if not structure.id:
            raise ValueError("The submitted structure data is missing a required identifier")
        existing_structure = await StructureDAO._find_structure_by_id(structure, tx)

        if existing_structure is None:
            raise NotFoundError(f"Structure with id {structure.id} does not exist")

        # Delete existing names
        delete_names_query = """
                MATCH (s:ResearchStructure {id: $structure_id})-[:HAS_NAME]->(n:OrganizationName)
                DETACH DELETE n
            """
        await tx.run(delete_names_query, structure_id=structure.id)

        # Create new names with literals
        create_names_query = """
                MATCH (s:ResearchStructure {id: $structure_id})
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
            structure_id=structure.id,
            names=[name.dict() for name in structure.names]
        )

        # Delete identifiers that are not in the new set
        delete_identifiers_query = """
                MATCH (s:ResearchStructure {id: $structure_id})-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
                WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
                DETACH DELETE i
            """
        identifier_types = [identifier.type.value for identifier in structure.identifiers]
        identifier_values = [identifier.value for identifier in structure.identifiers]
        await tx.run(
            delete_identifiers_query,
            structure_id=structure.id,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )

        # Create or update identifiers
        create_identifiers_query = """
                MATCH (s:ResearchStructure {id: $structure_id})
                UNWIND $identifiers AS identifier
                MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
                ON CREATE SET i = identifier
                ON MATCH SET i = identifier
                MERGE (s)-[:HAS_IDENTIFIER]->(i)
            """
        await tx.run(
            create_identifiers_query,
            structure_id=structure.id,
            identifiers=[identifier.dict() for identifier in structure.identifiers]
        )

    async def find_by_identifier(self, identifier_type: OrganizationIdentifierType,
                                 identifier_value: str) -> ResearchStructure | None:
        """
        Find a structure by an identifier

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
                        structure_data = record["s"]
                        names_data = record["names"]
                        identifiers_data = record["identifiers"]

                        names = [Literal(**name) for name in names_data]
                        identifiers = [OrganizationIdentifier(**identifier)
                                       for identifier in identifiers_data]

                        structure = ResearchStructure(
                            id=structure_data["id"],
                            identifiers=identifiers,
                            names=names
                        )

                        return structure
                    return None

    _find_by_identifier_query = """
        MATCH (s:ResearchStructure)-[:HAS_NAME]->(n:Literal)
        MATCH (s)-[:HAS_IDENTIFIER]->(i1:AgentIdentifier {type: $identifier_type, value: $identifier_value})
        MATCH (s)-[:HAS_IDENTIFIER]->(i2:AgentIdentifier)
        RETURN s, collect(n) as names, collect(i2) as identifiers
    """
