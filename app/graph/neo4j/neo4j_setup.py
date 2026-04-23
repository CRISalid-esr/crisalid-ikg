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
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_constraints)

    @classmethod
    async def _create_constraints(cls, tx: AsyncManagedTransaction):
        settings = get_app_settings()
        await cls._create_person_uid_constraint(tx)
        await cls._create_agent_identifier_unique_type_value_constraint(tx)
        await cls._create_journal_uid_constraint(tx)
        await cls._create_journal_identifier_uid_constraint(tx)
        await cls._create_journal_identifier_type_value_constraint(tx)
        # Potential issue : https://github.com/CRISalid-esr/crisalid-ikg/issues/157
        await cls._create_source_journal_uid_constraint(tx)
        await cls._create_source_person_uid_constraint(tx)
        await cls._create_source_person_identifier_unique_type_value_constraint(tx)
        await cls._create_source_organization_uid_constraint(tx)
        await cls._create_source_organization_identifier_unique_type_value_constraint(tx)
        # Idem https://github.com/CRISalid-esr/crisalid-ikg/issues/161
        await cls._create_concept_uid_constraint(tx)
        await cls._create_concept_uri_constraint(tx)
        await cls._create_document_uid_constraint(tx)
        await cls._create_institution_uid_constraint(tx)
        await cls._create_structured_physical_address_uid_constraint(tx)
        await cls._create_place_lat_lon_unique_constraint(tx)
        await cls._create_research_unit_uid_unique_constraint(tx)
        await cls._create_publication_identifier_unique_type_value_constraint(tx)
        await cls._create_source_issue_unique_source_identifier_source_constraint(tx)
        await cls._create_authority_organization_state_signature_constraint(tx)
        await cls._create_authority_organization_uid_constraint(tx)
        await cls._create_literal_value_language_type_constraint(tx)
        await cls._create_text_literal_type_key_constraint(tx)
        await cls._create_source_record_uid_constraint(tx)
        await cls._create_change_uid_constraint(tx)

        if settings.neo4j_edition == "community":
            return
        assert settings.neo4j_version == "enterprise"
        await cls._create_agent_identifier_type_constraint(tx)
        await cls._create_agent_identifier_value_constraint(tx)
        await cls._create_has_name_relationship_constraint(tx)
        await cls._create_source_record_represented_by_document_constraint(tx)

    @staticmethod
    async def _create_concept_uid_constraint(tx: AsyncManagedTransaction):
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
    async def _create_concept_uri_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT concept_uri_unique IF NOT EXISTS
        FOR (c:Concept) REQUIRE c.uri IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error("Error creating concept uri unique constraint: {}", e)
            raise e

    @staticmethod
    async def _create_person_uid_constraint(tx: AsyncManagedTransaction):
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
    async def _create_agent_identifier_type_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT agent_identifier_type_not_null IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.type IS NOT NULL
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier type not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_value_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT agent_identifier_value_not_null  IF NOT EXISTS
        FOR (a:AgentIdentifier) REQUIRE a.value IS NOT NULL
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating agent identifier value not null constraint: {e}")

    @staticmethod
    async def _create_agent_identifier_unique_type_value_constraint(tx: AsyncManagedTransaction):
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
    async def _create_has_name_relationship_constraint(tx: AsyncManagedTransaction):
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
    async def _create_journal_identifier_uid_constraint(tx: AsyncManagedTransaction):
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
    async def _create_journal_identifier_type_value_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT journal_identifier_type_value_unique IF NOT EXISTS
        FOR (j:JournalIdentifier) REQUIRE (j.type, j.value) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating journal identifier type/value unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_journal_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_journal_uid_unique IF NOT EXISTS
        FOR (j:SourceJournal) REQUIRE j.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating source journal uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_person_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_person_uid_unique IF NOT EXISTS
        FOR (p:SourcePerson) REQUIRE p.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating source person uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_person_identifier_unique_type_value_constraint(
            tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_person_identifier_unique_type_value IF NOT EXISTS
        FOR (i:SourcePersonIdentifier) REQUIRE (i.type, i.value) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                f"Error creating source person identifier unique type/value constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_organization_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_organization_uid_unique IF NOT EXISTS
        FOR (o:SourceOrganization) REQUIRE o.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating source organization uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_source_organization_identifier_unique_type_value_constraint(
            tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_organization_identifier_unique_type_value IF NOT EXISTS
        FOR (i:SourceOrganizationIdentifier) REQUIRE (i.type, i.value) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                f"Error creating source organization identifier unique type/value constraint: {e}")
            raise e

    @staticmethod
    async def _create_document_uid_constraint(tx: AsyncManagedTransaction):
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
    async def _create_institution_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT institution_uid_unique IF NOT EXISTS
        FOR (i:Institution) REQUIRE i.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating institution uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_structured_physical_address_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT structured_physical_address_uid_unique IF NOT EXISTS
        FOR (a:StructuredPhysicalAddress) REQUIRE a.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating StructuredPhysicalAddress uid unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_place_lat_lon_unique_constraint(tx: AsyncManagedTransaction):
        query = """
            CREATE CONSTRAINT place_latitude_longitude_unique IF NOT EXISTS
            FOR (p:Place) REQUIRE (p.latitude, p.longitude) IS UNIQUE;
            """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(f"Error creating Place (latitude, longitude) unique constraint: {e}")
            raise e

    @staticmethod
    async def _create_research_unit_uid_unique_constraint(
            tx: AsyncManagedTransaction
    ):
        query = """
        CREATE CONSTRAINT research_unit_uid_unique IF NOT EXISTS
        FOR (r:ResearchUnit)
        REQUIRE r.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating ResearchUnit uid unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_source_record_represented_by_document_constraint(tx: AsyncManagedTransaction):
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

    @staticmethod
    async def _create_source_record_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT source_record_uid_unique IF NOT EXISTS
        FOR (s:SourceRecord)
        REQUIRE s.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating SourceRecord uid unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_change_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT change_uid_unique IF NOT EXISTS
        FOR (c:Change)
        REQUIRE c.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating Change uid unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_authority_organization_state_signature_constraint(
            tx: AsyncManagedTransaction
    ):
        query = """
        CREATE CONSTRAINT authority_org_state_signature_unique IF NOT EXISTS
        FOR (o:AuthorityOrganizationState)
        REQUIRE o.identifier_signature IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating AuthorityOrganizationState identifier_signature unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_authority_organization_uid_constraint(
            tx: AsyncManagedTransaction
    ):
        query = """
        CREATE CONSTRAINT authority_organization_uid_unique IF NOT EXISTS
        FOR (o:AuthorityOrganization)
        REQUIRE o.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating AuthorityOrganization uid unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_literal_value_language_type_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT literal_value_language_type_unique IF NOT EXISTS
        FOR (l:Literal)
        REQUIRE (l.value, l.language, l.type) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating Literal value/language/type unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_text_literal_type_key_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT textliteral_type_key_unique IF NOT EXISTS
        FOR (t:TextLiteral)
        REQUIRE (t.key, t.type) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating TextLiteral key unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_publication_identifier_unique_type_value_constraint(
            tx: AsyncManagedTransaction
    ):
        query = """
        CREATE CONSTRAINT publication_identifier_unique_type_value IF NOT EXISTS
        FOR (p:PublicationIdentifier)
        REQUIRE (p.type, p.value) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating PublicationIdentifier type/value unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_source_issue_unique_source_identifier_source_constraint(
            tx: AsyncManagedTransaction
    ):
        query = """
        CREATE CONSTRAINT source_issue_unique_source_identifier_source IF NOT EXISTS
        FOR (i:SourceIssue)
        REQUIRE (i.source_identifier, i.source) IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating SourceIssue source_identifier/source unique constraint: "
                f"{e}"
            )
            raise e

    @staticmethod
    async def _create_journal_uid_constraint(tx: AsyncManagedTransaction):
        query = """
        CREATE CONSTRAINT journal_uid_unique IF NOT EXISTS
        FOR (j:Journal)
        REQUIRE j.uid IS UNIQUE;
        """
        try:
            await tx.run(query=query)
        except DatabaseError as e:
            logger.error(
                "Error creating Journal uid unique constraint: "
                f"{e}"
            )
            raise e
