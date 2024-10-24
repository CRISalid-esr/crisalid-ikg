from loguru import logger
from neo4j.exceptions import Neo4jError

from app.config import get_app_settings
from app.errors.reference_owner_not_found_error import ReferenceOwnerNotFoundError
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.concepts.concept_service import ConceptService
from app.services.source_journals.source_journal_service import SourceJournalService
from app.signals import source_record_created


class SourceRecordService:
    """
    Service to handle operations on source records data
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
        person = await self._handle_source_record_owner(harvested_for)
        await self._handle_source_record_subjects(source_record)
        await self._handle_source_record_journal(source_record)
        await self._handle_source_record(source_record, person)
        return source_record

    async def _handle_source_record(self, source_record, person):
        source_record_dao: SourceRecordDAO = self._get_dao_factory().get_dao(SourceRecord)
        source_record_id, status, _ = await source_record_dao.create(source_record=source_record,
                                                                     harvested_for=person)
        if status is SourceRecordDAO.Status.CREATED:
            await source_record_created.send_async(self, source_record_id=source_record_id)

    async def _handle_source_record_journal(self, source_record: SourceRecord) -> None:
        if not source_record.issue or not source_record.issue.journal:
            return
        source_journal = source_record.issue.journal
        source_journal_service = SourceJournalService()
        registered_source_journal = None
        try:
            registered_source_journal = await \
                source_journal_service.create_or_update_source_journal(
                    source_journal)
        except ValueError as e:
            logger.error(
                f"Invalid data error while creating or updating source journal {source_journal} :"
                f" {e}")
        except Neo4jError as e:
            logger.error(
                f"Database error while creating or updating source journal {source_journal} : {e}")
        source_record.issue.journal = registered_source_journal

    async def _handle_source_record_subjects(self, source_record: SourceRecord) -> None:
        concept_service = ConceptService()
        registered_concepts = []
        for subject in source_record.subjects:
            try:
                concept = await concept_service.create_or_update_concept(subject)
                registered_concepts.append(concept)
            except ValueError as e:
                logger.error(f"Invalid data error while creating or updating concept {subject} :"
                             f" {e}")
            except Neo4jError as e:
                logger.error(f"Database error while creating or updating concept {subject} : {e}")
        source_record.subjects = registered_concepts

    async def _handle_source_record_owner(self, harvested_for: Person) -> Person:
        factory = self._get_dao_factory()
        people_dao: PersonDAO = factory.get_dao(Person)
        person = await people_dao.find(harvested_for)
        if not person:
            raise ReferenceOwnerNotFoundError(f"Person with uid {harvested_for.uid} does not exist")
        return person

    async def get_source_record(self, source_record_uid: str) -> SourceRecord:
        """
        Get a source record from the graph database
        :param source_record_uid: source record uid
        :return: Pydantic SourceRecord object
        """
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        return await dao.get(source_record_uid)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
