from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.signals import source_record_created


class SourceRecordService:
    """
    Service to handle operations on people data
    """

    async def create_source_record(self, source_record: SourceRecord,
                                   harvested_for: Person) -> SourceRecord:
        """
        Create a source bibliographic record in the graph database
        from a Pydantic SourceRecord object and a Pydantic Person object
        :param source_record: Pydantic SourceRecord object
        :param harvested_for: Pydantic Person object.
                The person the reference has been harvested for
        :return:
        """
        factory = self._get_dao_factory()
        people_dao: PersonDAO = factory.get_dao(Person)
        person = await people_dao.find(harvested_for)
        if not person:
            raise ValueError(f"Person with id {harvested_for.id} does not exist")
        source_record_dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        record_id, status, _ = await source_record_dao.create(source_record=source_record,
                                                              harvested_for=person)
        if status is SourceRecordDAO.Status.CREATED:
            await source_record_created.send_async(self, payload=record_id)
        return source_record

    async def get_source_record(self, source_record_id: str) -> SourceRecord:
        """
        Get a source record from the graph database
        :param source_record_id: source record id
        :return: Pydantic SourceRecord object
        """
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        return await dao.get(source_record_id)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
