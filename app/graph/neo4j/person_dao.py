from typing import Tuple, NamedTuple

from loguru import logger
from neo4j import AsyncSession, AsyncManagedTransaction
from neo4j.exceptions import ConstraintError, ClientError, Neo4jError, DatabaseError

from app.config import get_app_settings
from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.agent_identifiers import PersonIdentifier
from app.models.identifier_types import PersonIdentifierType
from app.models.memberships import Membership
from app.models.people import Person
from app.models.people_names import PersonName
from app.services.identifiers.identifier_service import AgentIdentifierService


class PersonDAO(Neo4jDAO):
    """
    Data access object for people and the neo4j database
    """

    class UpdateStatus(NamedTuple):
        """
        Update status details
        """
        identifiers_changed: bool
        names_changed: bool
        memberships_changed: bool

    async def get(self, person_id: str) -> Person | None:
        """
        Get a person from the graph database

        :param person_id: person id
        :return: person object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await PersonDAO._get_person_by_id(tx, person_id)

    @classmethod
    async def _get_person_by_id(cls, tx, person_id: str) -> Person | None:
        result = await tx.run(
            load_query("get_person_by_id"),
            person_id=person_id
        )
        record = await result.single()
        if record:
            return cls._hydrate(record)
        return None

    @staticmethod
    def _hydrate(record: dict) -> Person:
        person_data = record["person"]
        names_data = record["names"]
        identifiers_data = record["identifiers"]
        memberships_data = record["memberships"]
        names = [PersonName(**name) for name in names_data]
        identifiers = [PersonIdentifier(**identifier)
                       for identifier in identifiers_data]
        memberships = []
        for membership_data in memberships_data:
            research_structure = membership_data["research_structure"]
            if research_structure is None:
                continue
            memberships.append(
                Membership(
                    entity_id=membership_data["research_structure"]['id']
                )
            )
        person = Person(
            id=person_data["id"],
            identifiers=identifiers,
            names=names,
            memberships=memberships
        )
        return person

    @staticmethod
    async def _person_exists(tx: AsyncManagedTransaction, person_id: str) -> bool:
        result = await tx.run(
            load_query("person_exists"),
            person_id=person_id
        )
        record = await result.single()
        return record is not None

    async def create(self, person: Person) -> Tuple[str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create  a person in the graph database

        :param person: person object
        :return: person id and operation status
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_person_transaction, person)
        return person.id, PersonDAO.Status.CREATED, None

    async def update(self, person: Person) -> Tuple[str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Update a person in the graph database

        :param person: person object
        :return: person id, operation status and update status details
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                update_status = await session.write_transaction(self._update_person_transaction,
                                                                person)
        return person.id, PersonDAO.Status.UPDATED, update_status

    async def create_or_update(self, person: Person) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create or update a person in the graph database

        :param person: person object
        :return: person id, operation status and update status details
        """
        status = None
        update_status = None
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                try:
                    await session.write_transaction(self._create_person_transaction, person)
                    status = self.Status.CREATED
                except ConflictError:
                    update_status = await session.write_transaction(self._update_person_transaction,
                                                                    person)
                    status = self.Status.UPDATED
        return person.id, status, update_status

    @staticmethod
    async def _create_person_transaction(tx: AsyncManagedTransaction, person: Person) -> None:
        person.id = person.id or AgentIdentifierService.compute_identifier_for(person)
        if not person.id:
            raise ValueError(f"Unable to compute primary key for person {person}")
        person_exists = await PersonDAO._person_exists(tx, person.id)
        if person_exists:
            raise ConflictError(f"Person with id {person.id} already exists")
        create_person_query = load_query("create_person")
        try:
            await tx.run(
                create_person_query,
                person_id=person.id,
                names=[name.dict() for name in person.names],
                identifiers=[identifier.dict() for identifier in person.identifiers]
            )
        except ConstraintError as constraint_error:
            raise ConflictError(
                f"Schema constraint violation while creating person {person}") from constraint_error
        except ClientError as client_error:
            raise ValueError(
                f"Bad request error while creating person {person}") from client_error
        except Neo4jError as neo4j_error:
            raise DatabaseError(f"Database error while creating person {person}") from neo4j_error
        for membership in person.memberships:
            structure_id = AgentIdentifierService.compute_identifier_for(
                membership.research_structure
            )
            if structure_id:
                find_structure_query = load_query("find_structure_by_id")
                result = await tx.run(find_structure_query, structure_id=structure_id)
                structure = await result.single()
                if structure:
                    create_membership_query = load_query("create_membership")
                    await tx.run(create_membership_query,
                                 person_id=person.id,
                                 structure_id=structure_id)
                else:
                    logger.error(f"Research structure with id {structure_id} not found")
            else:
                logger.error(
                    "Unable to compute primary key for research structure "
                    f"{membership.research_structure}"
                )

    @classmethod
    async def _update_person_transaction(cls, tx: AsyncSession,
                                         incoming_person: Person) -> UpdateStatus:
        incoming_person.id = incoming_person.id or AgentIdentifierService.compute_identifier_for(
            incoming_person)
        if not incoming_person.id:
            raise ValueError(f"Unable to compute primary key for person {incoming_person}")
        existing_person = await cls._get_person_by_id(tx, incoming_person.id)

        if existing_person is None:
            raise NotFoundError(f"Person with id {incoming_person.id} does not exist")
        await tx.run(load_query("delete_person_names"),
                     person_id=incoming_person.id)
        await tx.run(
            load_query("create_person_names"),
            person_id=incoming_person.id,
            names=[name.dict() for name in incoming_person.names]
        )
        existing_identifiers = existing_person.identifiers
        identifier_types = [identifier.type.value for identifier in incoming_person.identifiers]
        identifier_values = [identifier.value for identifier in incoming_person.identifiers]
        await tx.run(
            load_query("delete_person_identifiers"),
            person_id=incoming_person.id,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )
        await tx.run(
            load_query("create_person_identifiers"),
            person_id=incoming_person.id,
            identifiers=[identifier.dict() for identifier in incoming_person.identifiers]
        )
        identifiers_changed = AgentIdentifierService.identifiers_are_identical(
            existing_identifiers,
            incoming_person.identifiers
        )
        return PersonDAO.UpdateStatus(
            identifiers_changed=identifiers_changed,
            names_changed=None,
            memberships_changed=None
        )

    async def find_person(self, person: Person) -> Person | None:
        """
        Find a person by one of its identifiers
        taking identifiers in the order defined in the settings
        :param person: person object
        :return: person object
        """
        settings = get_app_settings()
        identifier_order = settings.person_identifier_order
        for identifier_type in identifier_order:
            identifier = next((identifier for identifier in person.identifiers
                               if identifier.type == identifier_type), None)
            if identifier:
                found_person = await self.find_by_identifier(identifier.type, identifier.value)
                if found_person:
                    return found_person
        return None

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
                        load_query("find_person_by_identifier"),
                        identifier_type=identifier_type.value,
                        identifier_value=identifier_value
                    )
                    record = await result.single()
                    if record is not None:
                        return PersonDAO._hydrate(record)
                    return None
