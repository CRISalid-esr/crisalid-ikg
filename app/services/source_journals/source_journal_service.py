from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.source_journal_dao import SourceJournalDAO
from app.models.source_journal import SourceJournal


class SourceJournalService:
    """
    Service to handle operations on source journals data
    """

    async def create_or_update_source_journal(self, source_journal: SourceJournal) -> SourceJournal:
        """
        Create a source scientific journal in the graph database
        from a Pydantic SourceJournal object
        :param source_journal: Pydantic SourceJournal object
        :return:
        """
        factory = self._get_dao_factory()
        source_journal_dao: SourceJournalDAO = factory.get_dao(SourceJournal)
        assert source_journal.uid, "Source journal uid should have been computed before from" \
                                   f"{source_journal.source} and {source_journal.source_identifier}"
        existing_source_journal = await source_journal_dao.get_by_uid(source_journal.uid)
        if existing_source_journal:
            return await source_journal_dao.update(source_journal)
        return await source_journal_dao.create(source_journal)

    @staticmethod
    def _get_dao_factory() -> DAOFactory:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
