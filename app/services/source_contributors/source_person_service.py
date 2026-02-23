from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_person_dao import SourcePersonDAO
from app.models.source_people import SourcePerson


class SourcePersonService:
    """
    Service to handle operations on source journals data
    """

    async def create_or_update_source_person(self, source_person: SourcePerson) -> (
            SourcePerson):
        """
        Create a source contributor in the graph database from a Pydantic SourceContributor object
        :param source_person: Pydantic SourceContributor object
        :return:
        """
        factory = self._get_dao_factory()
        source_person_dao: SourcePersonDAO = factory.get_dao(SourcePerson)
        assert source_person.uid, \
            "Source person uid should have been computed before from" \
            f"{source_person.source.value} and {source_person.source_identifier}"
        source_person_exists = await source_person_dao.source_person_exists(source_person.uid)
        if source_person_exists:
            return await source_person_dao.update(source_person)
        return await source_person_dao.create(source_person)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
