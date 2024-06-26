from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.people_dao import PeopleDAO
from app.models.people import Person


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
        factory = self._get_people_dao()
        dao: PeopleDAO = factory.get_dao(Person)
        return await dao.create(person)

    async def update_person(self, person: Person) -> Person:
        """
        Update a person in the graph database from a Pydantic Person object
        :param person: Pydantic Person object
        :return:
        """
        factory = self._get_people_dao()
        dao: PeopleDAO = factory.get_dao(Person)
        return await dao.update(person)

    @staticmethod
    def _get_people_dao() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
