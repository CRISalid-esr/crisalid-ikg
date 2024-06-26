from neo4j import AsyncSession

from app.config import get_app_settings
from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.models.people_names import PersonName


class PeopleDAO(Neo4jDAO):
    """
    Data access object for people and the neo4j database
    """

    async def create(self, person: Person) -> Person:
        """
        Create  a person in the graph database

        :param person: person object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_person_transaction, person)
        return person

    async def update(self, person: Person) -> Person:
        """
        Update a person in the graph database

        :param person: person object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._update_person_transaction, person)
        return person

    @staticmethod
    async def _create_person_transaction(tx: AsyncSession, person: Person):
        person.id = await PeopleDAO._compute_person_id(person)
        if not person.id:
            raise ValueError("The submitted person data is missing a required identifier")
        existing_person = await PeopleDAO._find_person_by_id(person, tx)

        if existing_person is not None:
            raise ConflictError(f"Person with id {person.id} already exists")

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
            person_id=person.id,
            names=[name.dict() for name in person.names],
            identifiers=[identifier.dict() for identifier in person.identifiers]
        )
        return person

    @staticmethod
    async def _find_person_by_id(person, tx):
        find_person_query = """
                MATCH (p:Person {id: $person_id})
                RETURN p
                """
        result = await tx.run(find_person_query, person_id=person.id)
        record = await result.single()
        return record

    @staticmethod
    async def _compute_person_id(person):
        settings = get_app_settings()
        identifier_order = settings.people_identifier_order
        person_id = None
        for identifier_type in identifier_order:
            if identifier_type in [identifier.type for identifier in person.identifiers]:
                selected_identifier = next(
                    identifier for identifier in person.identifiers
                    if identifier.type == identifier_type
                )
                person_id = f"{selected_identifier.type.value}-{selected_identifier.value}"
                break
        return person_id

    @staticmethod
    async def _update_person_transaction(tx: AsyncSession, person: Person):
        if person.id is None:
            person.id = await PeopleDAO._compute_person_id(person)
        if not person.id:
            raise ValueError("The submitted person data is missing a required identifier")
        existing_person = await PeopleDAO._find_person_by_id(person, tx)

        if existing_person is None:
            raise NotFoundError(f"Person with id {person.id} does not exist")

        delete_names_query = """
                MATCH (p:Person {id: $person_id})-[:HAS_NAME]->(n:PersonName)
                DETACH DELETE n
            """
        await tx.run(delete_names_query, person_id=person.id)

        create_names_query = """
                MATCH (p:Person {id: $person_id})
                UNWIND $names AS name
                CREATE (n:PersonName {first_names: name.first_names, family_names: name.family_names, other_names: name.other_names})
                CREATE (p)-[:HAS_NAME]->(n)
            """
        await tx.run(
            create_names_query,
            person_id=person.id,
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
            person_id=person.id,
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
            person_id=person.id,
            identifiers=[identifier.dict() for identifier in person.identifiers]
        )

    async def find_by_identifier(self, identifier_type: PersonIdentifierType,
                                 identifier_value: str) -> Person | None:
        """
        Find a person by an identifier

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
                        person_data = record["p"]
                        names_data = record["names"]
                        identifiers_data = record["identifiers"]

                        names = [PersonName(**name) for name in names_data]
                        identifiers = [PersonIdentifier(**identifier)
                                       for identifier in identifiers_data]

                        person = Person(
                            id=person_data["id"],
                            identifiers=identifiers,
                            names=names
                        )

                        return person
                    return None

    _find_by_identifier_query = """
        MATCH (p:Person)-[:HAS_NAME]->(n:PersonName)
        MATCH (p)-[:HAS_IDENTIFIER]->(i1:AgentIdentifier {type: $identifier_type, value: $identifier_value})
        MATCH (p)-[:HAS_IDENTIFIER]->(i2:AgentIdentifier)
        RETURN p, collect(n) as names, collect(i2) as identifiers
    """
