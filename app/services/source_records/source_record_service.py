from loguru import logger

from app.config import get_app_settings
from app.errors.database_error import DatabaseError
from app.errors.reference_owner_not_found_error import ReferenceOwnerNotFoundError
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.concepts.concept_service import ConceptService
from app.services.source_contributors.source_organization_service import SourceOrganizationService
from app.services.source_contributors.source_person_service import SourcePersonService
from app.services.source_journals.source_journal_service import SourceJournalService
from app.signals import source_record_created, source_record_updated


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
        await self._handle_source_record_contributors(source_record)
        await self._handle_source_record_affiliations(source_record)
        await self._handle_source_record_subjects(source_record)
        await self._handle_source_record_journal(source_record)
        await self._create_source_record(source_record, person)
        await self._update_source_record_contributions(source_record)
        return source_record

    async def update_source_record(self, source_record: SourceRecord,
                                   harvested_for: Person) -> SourceRecord:
        """
        Update a source bibliographic record in the graph database
        from a Pydantic SourceRecord object and a Pydantic Person object
        :param source_record: Pydantic SourceRecord object
        :param harvested_for: Pydantic Person object.
               The person the reference has been harvested for
        :return:
        """
        person = await self._handle_source_record_owner(harvested_for)
        await self._handle_source_record_contributors(source_record)
        await self._handle_source_record_affiliations(source_record)
        await self._handle_source_record_subjects(source_record)
        await self._handle_source_record_journal(source_record)
        await self._update_source_record(source_record, person)
        await self._update_source_record_contributions(source_record)
        return source_record

    async def _create_source_record(self, source_record, person):
        source_record_dao: SourceRecordDAO = self._get_dao_factory().get_dao(SourceRecord)
        source_record_id, status, _ = await source_record_dao.create(source_record=source_record,
                                                                     harvested_for=person)
        # FIXME call signal after contributions update
        if status is SourceRecordDAO.Status.CREATED:
            await source_record_created.send_async(self, source_record_id=source_record_id)

    async def _update_source_record_contributions(self, source_record):
        source_record_dao: SourceRecordDAO = self._get_dao_factory().get_dao(SourceRecord)
        await source_record_dao.delete_contributions(source_record.uid)
        for contribution in source_record.contributions:
            try:
                await source_record_dao.create_contribution(contribution, source_record.uid)
            except ValueError as e:
                logger.error(
                    f"Invalid data error while creating contribution {contribution} : {e}")
            except DatabaseError as e:
                logger.error(f"Database error while creating contribution {contribution} : {e}")

    async def _update_source_record(self, source_record, person):
        source_record_dao: SourceRecordDAO = self._get_dao_factory().get_dao(SourceRecord)
        await source_record_dao.update(source_record=source_record, harvested_for=person
                                       )
        await source_record_updated.send_async(self, source_record_id=source_record.uid)

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
        except DatabaseError as e:
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
            except DatabaseError as e:
                logger.error(f"Database error while creating or updating concept {subject} : {e}")
        source_record.subjects = registered_concepts

    async def _handle_source_record_contributors(self, source_record: SourceRecord) -> None:
        source_contributors_service = SourcePersonService()
        for i, contribution in enumerate(source_record.contributions):
            try:
                source_record.contributions[i].contributor = \
                    await source_contributors_service.create_or_update_source_person(
                        contribution.contributor)
            except ValueError as e:
                logger.error(
                    f"Invalid data error while creating or updating source contributor "
                    f"{contribution.contributor} : {e}")
            except DatabaseError as e:
                logger.error(
                    "Database error while creating or updating source contributor "
                    f"{contribution.contributor} : {e}")

    async def _handle_source_record_affiliations(self, source_record: SourceRecord) -> None:
        source_organization_service = SourceOrganizationService()
        for contribution in source_record.contributions:
            for i, source_organization in enumerate(contribution.affiliations):
                try:
                    contribution.affiliations[
                        i] = await source_organization_service.create_or_update_source_organization(
                        source_organization
                    )
                except ValueError as e:
                    logger.error(
                        "Invalid data error while creating or updating affiliation "
                        f"{source_organization} : {e}")
                except DatabaseError as e:
                    logger.error(
                        "Database error while creating or updating affiliation "
                        f"{source_organization} : {e}")

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

    async def source_record_exists(self, source_record_uid: str) -> bool:
        """
        Check if a source record exists in the graph database
        :param source_record_uid: source record uid
        :return: True if the source record exists, False otherwise
        """
        factory = self._get_dao_factory()
        dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        return await dao.source_record_exists(source_record_uid)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
