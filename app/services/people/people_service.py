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
from app.signals import person_created, person_identifiers_updated, person_unchanged, \
    person_deleted, person_updated, publications_to_be_updated


class PeopleService:
    """
    Service to handle operations on people data
    """

    async def signal_person_created(self, uid: str):
        """
        Dispatch the 'created' signal for a person.
        :param uid: The UID of the person
        """
        await person_created.send_async(self, payload=uid)

    async def signal_person_updated(self, uid: str):
        """
        Dispatch the 'updated' signal for a person.
        :param uid: The UID of the person
        """
        await person_updated.send_async(self, payload=uid)

    async def signal_person_unchanged(self, uid: str):
        """
        Dispatch the 'unchanged' signal for a person.
        :param uid: The UID of the person
        """
        await person_unchanged.send_async(self, payload=uid)

    async def signal_person_deleted(self, uid: str):
        """
        Dispatch the 'deleted' signal for a person.
        :param uid: The UID of the person
        """
        await person_deleted.send_async(self, payload=uid)

    async def signal_publications_to_be_updated(self, person_uid: str,
                                                harvesters: list[str] | None = None):
        """
        Dispatch the 'publications_to_be_updated' signal for a person.
        :param person_uid:
        :return:
        """
        await publications_to_be_updated.send_async(self, payload={
            "person_uid": person_uid,
            "harvesters": harvesters
        })

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
            existing_institution_uid = await institution_service.institution_uid(
                employment.institution)
            if existing_institution_uid is None:
                logger.warning(
                    f"Institution with identifiers {employment.institution.identifiers} not found")
                try:
                    institution = await institution_service.create_institution(
                        employment.institution)
                    employment.institution.uid = institution.uid
                except ValueError as e:
                    logger.error(f"Error creating institution: {e}")
                    continue
            else:
                employment.institution.uid = existing_institution_uid
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

    async def authenticate_identifier(self, person_uid: str,
                                      identifier_type: str, received_identifier: str,
                                      timestamp: str):
        """
        Authenticate a person's identifier
        """
        if identifier_type in [PersonIdentifierType.IDHALI.value,
                               PersonIdentifierType.IDHALS.value]:
            await self._authenticate_id_hal(person_uid, received_identifier,
                                            identifier_type, timestamp)

        elif identifier_type == PersonIdentifierType.ORCID.value:
            await self._authenticate_orcid(person_uid, received_identifier, timestamp)

        return

    async def _authenticate_id_hal(self, person_uid: str, received_id_hal: str,
                                   identifier_type: str, timestamp: str):
        """
        Authenticate a person's id_hal if necessary
        """
        person = await self.get_person(person_uid)
        hal_identifier = person.get_identifier(PersonIdentifierType.from_str(identifier_type))

        if hal_identifier is None:
            new_hal_identifier = PersonIdentifier(
                type=identifier_type,
                value=received_id_hal,
                authenticated=True,
                authentication_date=timestamp
            )
            person.identifiers.append(new_hal_identifier)

        elif hal_identifier.value == received_id_hal and hal_identifier.authenticated:
            logger.debug(f"{identifier_type} already authenticated for person {person_uid}.")
            raise ValueError(f"{identifier_type} {hal_identifier.value} is already authenticated "
                             f"for person {person_uid}.")

        else:
            hal_identifier = next(
                (id for id in person.identifiers if id.type.value == identifier_type), None
            )
            hal_identifier.value = received_id_hal
            hal_identifier.authenticated = True
            hal_identifier.authentication_date = timestamp

        await self.update_person(person)
        logger.debug(f"{identifier_type} authenticated for person {person_uid}.")
        return

    async def _authenticate_orcid(self, person_uid: str, received_orcid: str, timestamp: str):
        """
        Authenticate a person's Orcid if necessary
        """
        person = await self.get_person(person_uid)
        orcid_identifier = person.get_identifier(PersonIdentifierType.ORCID)

        if orcid_identifier is None:
            new_orcid_identifier = PersonIdentifier(
                type=PersonIdentifierType.ORCID,
                value=received_orcid,
                authenticated=True,
                authentication_date=timestamp
            )
            person.identifiers.append(new_orcid_identifier)

        elif orcid_identifier.value != received_orcid:
            logger.debug(
                f"Existing and received ORCID are different for person "
                f"{person_uid}. No authentication possible"
            )
            raise ValueError(
                f"Existing ORCID ({orcid_identifier.value}) and received ORCID ({received_orcid})"
                f" do not match for person {person_uid}. Authentication aborted."
            )

        elif orcid_identifier.value == received_orcid and orcid_identifier.authenticated:
            logger.debug(f"ORCID already authenticated for person {person_uid}.")
            raise ValueError(f"ORCID {orcid_identifier.value} is already authenticated "
                             f"for person {person_uid}.")

        else:
            orcid_identifier = next(
                (id for id in person.identifiers if
                 id.type.value == PersonIdentifierType.ORCID.value), None
            )
            orcid_identifier.authenticated = True
            orcid_identifier.authentication_date = timestamp

        await self.update_person(person)
        logger.debug(f"ORCID authenticated for person {person_uid}.")
        return

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
