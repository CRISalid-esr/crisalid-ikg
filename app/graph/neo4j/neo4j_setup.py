from loguru import logger
from neo4j import AsyncDriver
from neo4j.exceptions import DatabaseError

from app.config import get_app_settings
from app.graph.generic.setup import Setup
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion


class Neo4jSetup(Setup[AsyncDriver]):

    async def run(self):
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_constraints)

    @staticmethod
    async def _create_constraints(tx):
        settings = get_app_settings()
        await Neo4jSetup._create_person_id_constraint(tx)
        await Neo4jSetup._create_agent_identifier_unique_type_value_constraint(tx)
        if settings.neo4j_edition == "community":
            return
        assert settings.neo4j_version == "enterprise"
        await Neo4jSetup._create_agent_identifier_type_constraint(tx)
        await Neo4jSetup._create_agent_identifier_value_constraint(tx)

    @staticmethod
    async def _create_person_id_constraint(tx):
        query = """
        CREATE CONSTRAINT person_id_unique IF NOT EXISTS
        FOR (p:Person) REQUIRE p.id IS UNIQUE;
        """
        try:
            await tx.run(query)
        except DatabaseError as e:
            logger.error(f"Error creating person id unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_agent_identifier_type_constraint(tx):
        query = """
        CREATE CONSTRAINT agent_identifier_type_not_null IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.type IS NOT NULL
        """
        try:
            await tx.run(query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier type not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_value_constraint(tx):
        query = """
        CREATE CONSTRAINT agent_identifier_value_not_null  IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.value IS NOT NULL
        """
        try:
            await tx.run(query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier value not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_unique_type_value_constraint(tx):
        query = """
        CREATE CONSTRAINT agent_identifier_unique_type_value IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE (a.type, a.value) IS UNIQUE;
        """
        try:
            await tx.run(query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier unique type/value constraint: {e}")
            raise e
