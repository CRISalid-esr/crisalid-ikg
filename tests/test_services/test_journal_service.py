import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.journal_dao import JournalDAO
from app.models.journal import Journal
from app.models.journal_identifiers import JournalIdentifierFormat
from app.services.journals.journal_service import JournalService


@pytest.mark.asyncio
async def test_link_journal_identifiers_creates_journal(
        persisted_open_alex_source_journal,
        persisted_hal_source_journal,  # pylint: disable=unused-argument
        persisted_scanr_source_journal  # pylint: disable=unused-argument
):
    """
    Test the creation of a journal from a source journal by linking identifiers.
    :param persisted_open_alex_source_journal:
    :param persisted_hal_source_journal:
    :param persisted_scanr_source_journal:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    dao: JournalDAO = factory.get_dao(Journal)
    service = JournalService()
    matched_journal_uids = await service.link_journal_identifiers(
        None,
        persisted_open_alex_source_journal.uid)
    assert len(matched_journal_uids) == 1
    # check journal creation
    journal_reloaded = await dao.get_by_uid(matched_journal_uids[0])
    assert journal_reloaded is not None
    assert journal_reloaded.uid == matched_journal_uids[
        0]
    assert all(identifier.last_checked is not None for identifier in journal_reloaded.identifiers)
    assert (any(identifier.format == JournalIdentifierFormat.PRINT
                and identifier.value == "0007-4217"
                for identifier in journal_reloaded.identifiers))
    assert (any(
        identifier.format == JournalIdentifierFormat.ONLINE
        and identifier.value == "2241-0104" for
        identifier in journal_reloaded.identifiers))
    assert "Sample Journal Title" in journal_reloaded.titles
    assert journal_reloaded.publisher == "Example Publisher"
    assert journal_reloaded.uid == 'issn-l-0007-4217'
