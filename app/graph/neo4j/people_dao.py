from neo4j import AsyncSession
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.models.people import Person
from app.config import get_app_settings


class PeopleDAO(Neo4jDAO):

    async def create_or_update(self, person: Person):
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_or_update_person_transaction, person)

    @staticmethod
    async def _create_or_update_person_transaction(tx: AsyncSession, person: Person):
        settings = get_app_settings()
        identifier_order = settings.people_identifier_order

        person_id = None
        for identifier_type in identifier_order:
            if identifier_type in [identifier.type for identifier in person.identifiers]:
                selected_identifier = next(
                    identifier for identifier in person.identifiers if identifier.type == identifier_type
                )
                person_id = f"{selected_identifier.type.value}-{selected_identifier.value}"
                break

        if not person_id:
            raise ValueError("The submitted person data is missing a required identifier "
                             f"from the following list: {identifier_order}")

        find_person_query = """
                MATCH (p:Person {id: $person_id})
                RETURN p
                """

        result = await tx.run(find_person_query, person_id=person_id)
        record = await result.single()

        if record is None:
            # Create new person
            create_person_query = """
                        CREATE (p:Person {id: $person_id})
                        WITH p
                        UNWIND $names AS name
                        CREATE (n:PersonName {first_names: name.first_names, family_names: name.family_names, other_names: name.other_names})
                        CREATE (p)-[:HAS_NAME]->(n)
                        WITH p
                        UNWIND $identifiers AS identifier
                        CREATE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
                        CREATE (p)-[:HAS_IDENTIFIER]->(i)
                    """
            await tx.run(
                create_person_query,
                person_id=person_id,
                names=[name.dict() for name in person.names],
                identifiers=[identifier.dict() for identifier in person.identifiers]
            )
        else:
            # Update existing person
            await PeopleDAO._update_person(tx, person_id, person)

    @staticmethod
    async def _update_person(tx: AsyncSession, person_id: str, person: Person):
        delete_names_query = """
                MATCH (p:Person {id: $person_id})-[:HAS_NAME]->(n:PersonName)
                DETACH DELETE n
            """
        await tx.run(delete_names_query, person_id=person_id)

        create_names_query = """
                MATCH (p:Person {id: $person_id})
                UNWIND $names AS name
                CREATE (n:PersonName {first_names: name.first_names, family_names: name.family_names, other_names: name.other_names})
                CREATE (p)-[:HAS_NAME]->(n)
            """
        await tx.run(
            create_names_query,
            person_id=person_id,
            names=[name.dict() for name in person.names]
        )

        # Delete and recreate identifiers
        delete_identifiers_query = """
                MATCH (p:Person {id: $person_id})-[:HAS_IDENTIFIER]->(i:AgentIdentifier)
                WHERE NOT (i.type IN $identifier_types AND i.value IN $identifier_values)
                DETACH DELETE i
            """
        identifier_types = [identifier.type.value for identifier in person.identifiers]
        identifier_values = [identifier.value for identifier in person.identifiers]
        await tx.run(
            delete_identifiers_query,
            person_id=person_id,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )

        create_identifiers_query = """
                MATCH (p:Person {id: $person_id})
                UNWIND $identifiers AS identifier
                MERGE (i:AgentIdentifier {type: identifier.type, value: identifier.value})
                ON CREATE SET i = identifier
                ON MATCH SET i = identifier
                MERGE (p)-[:HAS_IDENTIFIER]->(i)
            """
        await tx.run(
            create_identifiers_query,
            person_id=person_id,
            identifiers=[identifier.dict() for identifier in person.identifiers]
        )

