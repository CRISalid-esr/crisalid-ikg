from typing import cast

from loguru import logger

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.employments import Employment
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.services.organizations.institution_service import InstitutionService
from app.amqp.message_mode import MessageMode
from app.signals import person_created, person_identifiers_updated, person_unchanged, \
    person_deleted, person_identifier_removed, person_updated, publications_to_be_updated


class PeopleService:
    """
    Service to handle operations on people data
    """

    async def signal_person_created(self, uid: str):
        """
        Dispatch the 'created' signal for a person.
        :param uid: The UID of the person
        """
        await person_created.send_async(self, payload=uid, mode=MessageMode.BATCH)

    async def signal_person_updated(self, uid: str):
        """
        Dispatch the 'updated' signal for a person.
        :param uid: The UID of the person
        """
        await person_updated.send_async(self, payload=uid, mode=MessageMode.BATCH)

    async def signal_person_unchanged(self, uid: str):
        """
        Dispatch the 'unchanged' signal for a person.
        :param uid: The UID of the person
        """
        await person_unchanged.send_async(self, payload=uid, mode=MessageMode.BATCH)

    async def signal_person_deleted(self, uid: str):
        """
        Dispatch the 'deleted' signal for a person.
        :param uid: The UID of the person
        """
        await person_deleted.send_async(self, payload=uid, mode=MessageMode.BATCH)

    async def signal_publications_to_be_updated(self, person_uid: str,
                                                harvesters: list[str] | None = None,
                                                mode: MessageMode = MessageMode.BATCH):
        """
        Dispatch the 'publications_to_be_updated' signal for a person.
        :param person_uid:
        :param harvesters:
        :param mode: message mode for the outbound retrieval task
        :return:
        """
        await publications_to_be_updated.send_async(self, payload={
            "person_uid": person_uid,
            "harvesters": harvesters
        }, mode=mode)

    async def create_person(self, person: Person) -> Person:
        """
        Create a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        person.employments = await self._update_employers_institutions(person.employments)
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        person_uid, status, _ = await dao.create(person)
        if status is PersonDAO.Status.CREATED:
            await self.signal_publications_to_be_updated(person_uid)
            await self.signal_person_created(person_uid)
        return person

    async def update_person(self, person: Person) -> Person:
        """
        Update a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        person.employments = await self._update_employers_institutions(person.employments)
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        person_uid, status, update_status = await dao.update(person)
        if status is PersonDAO.Status.UPDATED and update_status.identifiers_changed:
            await self.signal_publications_to_be_updated(person_uid)
            await self.signal_person_updated(person_uid)
        else:
            await self.signal_person_unchanged(person_uid)
        return person

    async def create_or_update_person(self, person: Person) -> None:
        """
        Create a person if not exists, update otherwise
        :param person: Pydantic Person object
        :return:
        """
        person.employments = await self._update_employers_institutions(person.employments)
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        person_uid, status, update_status = await dao.create_or_update(person)
        if status is PersonDAO.Status.CREATED:
            await person_created.send_async(payload=person_uid)
        elif status is PersonDAO.Status.UPDATED and update_status.identifiers_changed:
            await person_identifiers_updated.send_async(payload=person_uid)
        else:
            await self.signal_person_unchanged(person_uid)

    async def _update_employers_institutions(
            self, employments: list[Employment]) -> list[Employment]:
        institution_service = InstitutionService()
        valid_employments = []
        for employment in employments:
            existing_uid = await institution_service.institution_uid(employment.entity_uid)
            if existing_uid is None:
                logger.warning(
                    f"Institution with uid {employment.entity_uid!r} not found, "
                    f"fetching from registry"
                )
                try:
                    await institution_service.create_institution(employment.entity_uid)
                except ValueError as e:
                    logger.error(f"Error creating institution: {e}")
                    continue
            valid_employments.append(employment)
        return valid_employments

    async def get_person(self, person_uid: str) -> Person:
        """
        Get a person from the graph database
        :param person_uid: person uid
        :return: Pydantic Person object
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        return await dao.get(person_uid)

    async def get_all_person_uids(self, external: bool | None = None) -> list[str]:
        """
        Retrieve all person UIDs from the graph database.

        :return: A list of all person UIDs.
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        return await dao.get_all_uids(external=external)

    async def find_external_internal_shared_identifiers(self) -> list[dict]:
        """
        List every AgentIdentifier shared between an external and an internal person.

        :return: list of dicts (external_uid, external_display_name, id_type, id_value,
            internal_uid, internal_display_name).
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        return await dao.find_external_internal_shared_identifiers()

    async def detach_external_shared_identifiers(self) -> int:
        """
        Detach, from external persons, every HAS_IDENTIFIER edge whose AgentIdentifier is also
        owned by an internal person, restoring one-owner-per-identifier.

        :return: number of HAS_IDENTIFIER relationships detached.
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = cast(PersonDAO, factory.get_dao(Person))
        return await dao.detach_external_shared_identifiers()

    # pylint: disable-next=too-many-arguments
    async def add_identifier(self, person_uid: str, identifier_type: str,
                             value: str, authenticated: bool, timestamp: str):
        """
        Add an identifier to a person (add-only: an existing identifier of the same type
        must be removed first — value changes are always remove + add).

        Any manual add is performed by a privileged user, so the identifier is at least
        validated; it is authenticated only when the message asserts it (never for idref,
        which has no authentication process).

        :param person_uid: UID of the person
        :param identifier_type: identifier type (enum string value)
        :param value: identifier value
        :param authenticated: whether the identifier was obtained through authentication
        :param timestamp: authentication date carried by the message
        """
        id_type = self._parse_identifier_type(identifier_type)
        person = await self.get_person(person_uid)
        existing_identifier = person.get_identifier(id_type)
        if existing_identifier is not None:
            raise ValueError(
                f"Person {person_uid} already has a {identifier_type} identifier "
                f"({existing_identifier.value}): remove it before adding a new one."
            )
        new_identifier = PersonIdentifier(type=id_type, value=value)
        self._stamp_identifier_flags(new_identifier, authenticated, timestamp)
        person.identifiers.append(new_identifier)
        await self.update_person(person)
        detached = await self._get_person_dao().detach_external_identifier_owner(
            id_type.value, value)
        if detached:
            logger.info(
                "Detached {} external HAS_IDENTIFIER edge(s) for identifier {}={} "
                "now owned by person {}",
                detached, id_type.value, value, person_uid)
        logger.debug("{} identifier added for person {}.", identifier_type, person_uid)

    # pylint: disable-next=too-many-arguments
    async def confirm_identifier(self, person_uid: str, identifier_type: str,
                                 value: str, authenticated: bool, timestamp: str):
        """
        Confirm (authenticate/validate) an existing identifier without changing its value.
        The stored value must equal the received one; value changes are always remove + add.
        Idempotent: re-confirming an already confirmed identifier refreshes its flags.

        :param person_uid: UID of the person
        :param identifier_type: identifier type (enum string value)
        :param value: identifier value carried by the message
        :param authenticated: whether the identifier was confirmed through authentication
        :param timestamp: authentication date carried by the message
        """
        id_type = self._parse_identifier_type(identifier_type)
        person = await self.get_person(person_uid)
        identifier = person.get_identifier(id_type)
        if identifier is None:
            raise ValueError(
                f"Person {person_uid} has no {identifier_type} identifier to confirm."
            )
        if identifier.value != value:
            raise ValueError(
                f"Existing {identifier_type} ({identifier.value}) and received ({value}) "
                f"do not match for person {person_uid}: "
                f"value changes require remove + add."
            )
        self._stamp_identifier_flags(identifier, authenticated, timestamp)
        await self.update_person(person)
        logger.debug("{} identifier confirmed for person {}.", identifier_type, person_uid)

    async def remove_identifier(self, person_uid: str, identifier_type: str, value: str):
        """
        Remove a specific (type, value) identifier from a person and emit the dedicated
        removal signal so harvested data keyed on that identifier gets cleaned up.

        :param person_uid: UID of the person
        :param identifier_type: identifier type (enum string value)
        :param value: identifier value carried by the message
        """
        id_type = self._parse_identifier_type(identifier_type)
        person = await self.get_person(person_uid)
        identifier = person.get_identifier(id_type)
        if identifier is None or identifier.value != value:
            raise ValueError(
                f"Person {person_uid} has no {identifier_type} identifier "
                f"with value {value}: nothing to remove."
            )
        removed = await self._get_person_dao().remove_person_identifier(
            person_uid, id_type.value, value)
        if not removed:
            raise ValueError(
                f"Identifier {identifier_type}={value} could not be removed "
                f"for person {person_uid}."
            )
        await person_identifier_removed.send_async(
            self,
            person_uid=person_uid,
            identifier_type=id_type.value,
            identifier_value=value,
            mode=MessageMode.INTERACTIVE)
        await person_updated.send_async(self, payload=person_uid,
                                        mode=MessageMode.INTERACTIVE)
        logger.debug("{} identifier removed for person {}.", identifier_type, person_uid)

    @staticmethod
    def _parse_identifier_type(identifier_type: str) -> PersonIdentifierType:
        """
        Resolve an identifier type string to its enum member or raise.
        """
        id_type = PersonIdentifierType.from_str(identifier_type)
        if id_type is None:
            raise ValueError(f"Unknown identifier type: {identifier_type}")
        return id_type

    @staticmethod
    def _stamp_identifier_flags(identifier: PersonIdentifier,
                                authenticated: bool, timestamp: str):
        """
        Stamp validation/authentication flags on an identifier: idref is only ever
        validated; other types are authenticated when the message asserts it,
        validated otherwise (a manual update by a privileged user counts as validation).
        """
        identifier.validated = True
        if authenticated and identifier.type != PersonIdentifierType.IDREF:
            identifier.authenticated = True
            identifier.authentication_date = timestamp

    def _get_person_dao(self) -> PersonDAO:
        return cast(PersonDAO, self._get_dao_factory().get_dao(Person))

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
