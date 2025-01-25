from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.models.people import Person
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

    async def signal_publications_to_be_updated(self, person_uid):
        """
        Dispatch the 'publications_to_be_updated' signal for a person.
        :param person_uid:
        :return:
        """
        await publications_to_be_updated.send_async(self, payload=person_uid)

    async def create_person(self, person: Person) -> Person:
        """
        Create a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = factory.get_dao(Person)
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
        factory = self._get_dao_factory()
        dao: PersonDAO = factory.get_dao(Person)
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
        factory = self._get_dao_factory()
        dao: PersonDAO = factory.get_dao(Person)
        person_uid, status, update_status = await dao.create_or_update(person)
        if status is PersonDAO.Status.CREATED:
            await person_created.send_async(payload=person_uid)
        elif status is PersonDAO.Status.UPDATED and update_status.identifiers_changed:
            await person_identifiers_updated.send_async(payload=person_uid)
        else:
            await self.signal_person_unchanged(person_uid)

    async def get_person(self, person_uid: str) -> Person:
        """
        Get a person from the graph database
        :param person_uid: person uid
        :return: Pydantic Person object
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = factory.get_dao(Person)
        return await dao.get(person_uid)

    async def get_all_person_uids(self) -> list[str]:
        """
        Retrieve all person UIDs from the graph database.

        :return: A list of all person UIDs.
        """
        factory = self._get_dao_factory()
        dao: PersonDAO = factory.get_dao(Person)
        return await dao.get_all_uids()

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
