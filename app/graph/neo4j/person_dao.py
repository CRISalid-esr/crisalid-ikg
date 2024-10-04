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

    async def get(self, person_uid: str) -> Person | None:
        """
        Get a person from the graph database

        :param person_uid: person uid
        :return: person object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await PersonDAO._get_person_by_uid(tx, person_uid)

    async def create(self, person: Person) -> Tuple[str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create  a person in the graph database

        :param person: person object
        :return: person uid and operation status
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_person_transaction, person)
        return person.uid, PersonDAO.Status.CREATED, None

    async def update(self, person: Person) -> Tuple[str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Update a person in the graph database

        :param person: person object
        :return: person uid, operation status and update status details
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                update_status = await session.write_transaction(self._update_person_transaction,
                                                                person)
        return person.uid, PersonDAO.Status.UPDATED, update_status

    async def create_or_update(self, person: Person) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create or update a person in the graph database

        :param person: person object
        :return: person uid, operation status and update status details
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
        return person.uid, status, update_status

    async def find(self, person: Person) -> Person | None:
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
        :return: person object or None
        """
        # pylint: disable=duplicate-code
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

    @classmethod
    async def _get_person_by_uid(cls, tx, person_uid: str) -> Person | None:
        result = await tx.run(
            load_query("get_person_by_uid"),
            person_uid=person_uid
        )
        record = await result.single()
        if record:
            return cls._hydrate(record)
        return None

    @staticmethod
    async def _person_exists(tx: AsyncManagedTransaction, person_uid: str) -> bool:
        result = await tx.run(
            load_query("person_exists"),
            person_uid=person_uid
        )
        record = await result.single()
        return record is not None

    @staticmethod
    async def _create_person_transaction(tx: AsyncManagedTransaction, person: Person) -> None:
        person.uid = person.uid or AgentIdentifierService.compute_uid_for(person)
        if not person.uid:
            raise ValueError(f"Unable to compute primary key for person {person}")
        person_exists = await PersonDAO._person_exists(tx, person.uid)
        if person_exists:
            raise ConflictError(f"Person with uid {person.uid} already exists")
        create_person_query = load_query("create_person")
        try:
            await tx.run(
                create_person_query,
                person_uid=person.uid,
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
            structure_uid = AgentIdentifierService.compute_uid_for(
                membership.research_structure
            )
            if structure_uid:
                find_structure_query = load_query("find_structure_by_uid")
                result = await tx.run(find_structure_query, structure_uid=structure_uid)
                structure = await result.single()
                if structure:
                    create_membership_query = load_query("create_membership")
                    await tx.run(create_membership_query,
                                 person_uid=person.uid,
                                 structure_uid=structure_uid)
                else:
                    logger.error(f"Research structure with uid {structure_uid} not found")
            else:
                logger.error(
                    "Unable to compute primary key for research structure "
                    f"{membership.research_structure}"
                )

    @classmethod
    async def _update_person_transaction(cls, tx: AsyncSession,
                                         incoming_person: Person) -> UpdateStatus:
        incoming_person.uid = incoming_person.uid or AgentIdentifierService.compute_uid_for(
            incoming_person)
        if not incoming_person.uid:
            raise ValueError(f"Unable to compute primary key for person {incoming_person}")
        existing_person = await cls._get_person_by_uid(tx, incoming_person.uid)

        if existing_person is None:
            raise NotFoundError(f"Person with uid {incoming_person.uid} does not exist")
        await tx.run(load_query("delete_person_names"),
                     person_uid=incoming_person.uid)
        await tx.run(
            load_query("create_person_names"),
            person_uid=incoming_person.uid,
            names=[name.dict() for name in incoming_person.names]
        )
        existing_identifiers = existing_person.identifiers
        identifier_types = [identifier.type.value for identifier in incoming_person.identifiers]
        identifier_values = [identifier.value for identifier in incoming_person.identifiers]
        await tx.run(
            load_query("delete_person_identifiers"),
            person_uid=incoming_person.uid,
            identifier_types=identifier_types,
            identifier_values=identifier_values
        )
        await tx.run(
            load_query("create_person_identifiers"),
            person_uid=incoming_person.uid,
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
                    entity_uid=membership_data["research_structure"]['uid']
                )
            )
        person = Person(
            uid=person_data["uid"],
            identifiers=identifiers,
            names=names,
            memberships=memberships
        )
        return person
