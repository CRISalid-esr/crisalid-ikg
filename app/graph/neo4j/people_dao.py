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
from app.services.organisations.structure_service import StructureService


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

    async def create_or_update(self, person: Person) -> Person:
        """
        Create or update a person in the graph database

        :param person: person object
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                local_identifier_value = person.get_identifier(PersonIdentifierType.LOCAL).value
                existing_person = await self.find_by_identifier(
                    PersonIdentifierType.LOCAL,
                    local_identifier_value
                )
                if existing_person:
                    await session.write_transaction(self._update_person_transaction, person)
                else:
                    await session.write_transaction(self._create_person_transaction, person)
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
                    CREATE (pn:PersonName)
                    WITH p, pn, name
                    UNWIND name.first_names AS first_name
                    CREATE (fn:Literal {value: first_name.value, language: first_name.language})
                    CREATE (pn)-[:HAS_FIRST_NAME]->(fn)
                    WITH p, pn, name
                    UNWIND name.last_names AS last_name
                    CREATE (ln:Literal {value: last_name.value, language: last_name.language})
                    CREATE (pn)-[:HAS_LAST_NAME]->(ln)
                    CREATE (p)-[:HAS_NAME]->(pn)
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
        for membership in person.memberships:
            structure_id = await StructureService.compute_structure_id(
                membership.research_structure
            )
            if structure_id:
                find_structure_query = """
                            MATCH (s:ResearchStructure {id: $structure_id})
                            RETURN s
                        """
                result = await tx.run(find_structure_query, structure_id=structure_id)
                structure = await result.single()

                if structure:
                    create_membership_query = """
                                MATCH (p:Person {id: $person_id})
                                MATCH (s:ResearchStructure {id: $structure_id})
                                CREATE (m:Membership)
                                CREATE (p)-[:HAS_MEMBERSHIP]->(m)
                                CREATE (m)-[:MEMBER_OF]->(s)
                            """
                    await tx.run(create_membership_query,
                                 person_id=person.id,
                                 structure_id=structure_id)

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

        # Delete existing names with associated literals
        delete_names_query = """
                MATCH (p:Person {id: $person_id})-[:HAS_NAME]->(n:PersonName)
                MATCH (n)-[:HAS_FIRST_NAME]->(fn:Literal)
                MATCH (n)-[:HAS_LAST_NAME]->(ln:Literal)
                DETACH DELETE n , fn, ln
            """
        await tx.run(delete_names_query, person_id=person.id)

        # Create new names with literals
        create_names_query = """
                MATCH (p:Person {id: $person_id})
                UNWIND $names AS name
                CREATE (pn:PersonName)
                WITH p, pn, name
                UNWIND name.first_names AS first_name
                CREATE (fn:Literal {value: first_name.value, language: first_name.language})
                CREATE (pn)-[:HAS_FIRST_NAME]->(fn)
                WITH p, pn, name
                UNWIND name.last_names AS last_name
                CREATE (ln:Literal {value: last_name.value, language: last_name.language})
                CREATE (pn)-[:HAS_LAST_NAME]->(ln)
                CREATE (p)-[:HAS_NAME]->(pn)
            """
        await tx.run(
            create_names_query,
            person_id=person.id,
            names=[name.dict() for name in person.names]
        )

        # Delete identifiers that are not in the new set
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

        # Create or update identifiers
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
        MATCH (p:Person)-[:HAS_IDENTIFIER]->(i1:AgentIdentifier {type: $identifier_type, value: $identifier_value})
        OPTIONAL MATCH (p)-[:HAS_NAME]->(n:PersonName)
        OPTIONAL MATCH (n)-[:HAS_FIRST_NAME]->(fn:Literal)
        OPTIONAL MATCH (n)-[:HAS_LAST_NAME]->(ln:Literal)
        MATCH (p)-[:HAS_IDENTIFIER]->(i2:AgentIdentifier)
        WITH 
          p, 
          n, 
          i2, 
          fn, 
          ln,
          COLLECT(DISTINCT {value: fn.value, language: fn.language}) AS first_names,
          COLLECT(DISTINCT {value: ln.value, language: ln.language}) AS last_names
        WITH 
          p, 
          n, 
          i2, 
          COLLECT(DISTINCT {
            name: id(n), 
            first_names: first_names, 
            last_names: last_names
          }) AS names
        RETURN 
          p, 
          COLLECT(DISTINCT i2) AS identifiers, 
          names
    """
