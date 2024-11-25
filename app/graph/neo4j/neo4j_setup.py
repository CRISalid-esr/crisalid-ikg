from loguru import logger
from neo4j import AsyncDriver, AsyncManagedTransaction
from neo4j.exceptions import DatabaseError

from app.config import get_app_settings
from app.graph.generic.setup import Setup
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion


class Neo4jSetup(Setup[AsyncDriver]):
    """
    Class to setup the Neo4j database
    """

    async def run(self):
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_constraints)

    @classmethod
    async def _create_constraints(cls, tx:AsyncManagedTransaction):
        settings = get_app_settings()
        await cls._create_person_uid_constraint(tx)
        await cls._create_agent_identifier_unique_type_value_constraint(tx)
        await cls._create_journal_identifier_uid_constraint(tx)
        await cls._create_source_journal_source_identifier_constraint(tx)
        await cls._create_concept_uid_constraint(tx)
        await cls._create_document_uid_constraint(tx)

        if settings.neo4j_edition == "community":
            return
        assert settings.neo4j_version == "enterprise"
        await cls._create_agent_identifier_type_constraint(tx)
        await cls._create_agent_identifier_value_constraint(tx)
        await cls._create_has_name_relationship_constraint(tx)
        await cls._create_source_record_represented_by_document_constraint(tx)

    @staticmethod
    async def _create_concept_uid_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT concept_uid_unique IF NOT EXISTS
        FOR (c:Concept) REQUIRE c.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating concept uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_person_uid_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT person_uid_unique IF NOT EXISTS
        FOR (p:Person) REQUIRE p.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating person uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_agent_identifier_type_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT agent_identifier_type_not_null IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.type IS NOT NULL
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier type not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_value_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT agent_identifier_value_not_null  IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.value IS NOT NULL
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier value not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_unique_type_value_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT agent_identifier_unique_type_value IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE (a.type, a.value) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier unique type/value constraint: {e}")
            raise e

    @staticmethod
    async def _create_has_name_relationship_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT unique_has_name_relationship IF NOT EXISTS
        FOR ()-[r:HAS_NAME]->()
        REQUIRE (startNode(r), endNode(r)) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating has name relationship constraint: {e}")
            raise e

    @staticmethod
    async def _create_journal_identifier_uid_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT journal_identifier_uid_unique IF NOT EXISTS
        FOR (j:JournalIdentifier) REQUIRE j.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating journal identifier uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_journal_source_identifier_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_journal_source_identifier_unique IF NOT EXISTS
        FOR (j:SourceJournal) REQUIRE j.source_identifier IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating source journal source identifier unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_document_uid_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT document_uid_unique IF NOT EXISTS
        FOR (d:Document) REQUIRE d.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating document uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_record_represented_by_document_constraint(tx:AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_record_represented_by_document_unique IF NOT EXISTS
        FOR ()-[r:REPRESENTED_BY]->()
        REQUIRE (startNode(r), endNode(r)) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error("Error creating source record "
                         f"represented by document unique constraint: {e}")
            raise e
