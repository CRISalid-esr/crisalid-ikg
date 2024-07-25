from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.people_dao import PeopleDAO
from app.models.people import Person
from app.signals import person_created, person_identifiers_updated


class PeopleService:
    """
    Service to handle operations on people data
    """

    async def create_person(self, person: Person) -> Person:
        """
        Create a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_dao_factory()
        dao: PeopleDAO = factory.get_dao(Person)
        person_id, status, _ = await dao.create(person)
        if status is PeopleDAO.Status.CREATED:
            await person_created.send_async(self, payload=person_id)
        return person

    async def update_person(self, person: Person) -> Person:
        """
        Update a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_dao_factory()
        dao: PeopleDAO = factory.get_dao(Person)
        person_id, status, update_status = await dao.update(person)
        if status is PeopleDAO.Status.UPDATED and update_status.identifiers_changed:
            await person_identifiers_updated.send_async(self, payload=person_id)
        return person

    async def create_or_update_person(self, person: Person) -> None:
        """
        Create a person if not exists, update otherwise
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_dao_factory()
        dao: PeopleDAO = factory.get_dao(Person)
        person_id, status, update_status = await dao.create_or_update(person)
        if status is PeopleDAO.Status.CREATED:
            await person_created.send_async(payload=person_id)
        elif status is PeopleDAO.Status.UPDATED and update_status.identifiers_changed:
            await person_identifiers_updated.send_async(payload=person_id)

    async def get_person(self, person_id: str) -> Person:
        """
        Get a person from the graph database
        :param person_id: person id
        :return: Pydantic Person object
        """
        factory = self._get_dao_factory()
        dao: PeopleDAO = factory.get_dao(Person)
        return await dao.get(person_id)

    async def create_or_update_person(self, person: Person) -> Person:
        """
        Create a person if not exists, update otherwise
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_people_dao()
        dao: PeopleDAO = factory.get_dao(Person)
        return await dao.create_or_update(person)

    @staticmethod
    def _get_dao_factory() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
