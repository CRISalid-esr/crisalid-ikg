import time

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.journal_dao import JournalDAO
from app.graph.neo4j.source_journal_dao import SourceJournalDAO
from app.models.identifier_types import JournalIdentifierType
from app.models.journal import Journal
from app.models.journal_identifiers import JournalIdentifier
from app.models.source_journal import SourceJournal
from app.services.journals.issn_service import ISSNService


class JournalService:
    """
    Service to handle operations on journals data
    """

    # constructor. get app settings and take issn_check_delay parameter
    def __init__(self):
        settings = get_app_settings()
        self.issn_check_delay = settings.issn_check_delay
        self.issn_service = ISSNService()
        self.journal_dao: JournalDAO = self._get_dao_factory().get_dao(Journal)

    async def link_journal_identifiers(self, _, source_journal_uid):
        """
        Create a source scientific journal in the graph database
        from a Pydantic SourceJournal object
        :param source_journal: Pydantic SourceJournal object
        :return:
        """
        factory = self._get_dao_factory()
        source_journal_dao: SourceJournalDAO = factory.get_dao(SourceJournal)
        source_journal = await source_journal_dao.get_by_uid(source_journal_uid)
        identifiers = source_journal.identifiers
        for identifier in identifiers:
            if identifier.type == JournalIdentifierType.ISSN:
                # last_checked is a timestamp (int)
                last_checked = identifier.last_checked
                # if last_checked is None
                # or time since last_checked is greater than issn_check_delay
                if last_checked is None or (time.time() - last_checked) > self.issn_check_delay:
                    # check the related journal exists or create it
                    await self._create_or_update_journal_from(source_journal, identifier)
        return identifiers

    async def _create_or_update_journal_from(self, journal: SourceJournal,
                                             identifier: JournalIdentifier) -> Journal | None:
        """
        Check the identifier and update the last_checked timestamp
        :param identifier: JournalIdentifier object
        :return:
        """
        issn_info = await self.issn_service.check_identifier(identifier)
        if issn_info.errors:
            # if there are errors, set last_checked to None
            identifier.last_checked = None
            # TODO update the identifier in the graph
            return None
        identifier.last_checked = int(time.time())
        # TODO update the identifier in the graph
        # ISSN portal RDF pages do not provide publisher information for now
        issn_info.publisher = journal.publisher
        journal = Journal.from_issn_info(issn_info)
        existing_journal = await self.journal_dao.get_by_uid(journal.uid)
        if existing_journal:
            await self.journal_dao.update(journal)
        else:
            await self.journal_dao.create(journal)
        return journal

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
