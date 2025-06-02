import asyncio
from random import shuffle

import typer

from app.commands import with_app_lifecycle
from app.services.journals.journal_service import JournalService
from app.services.source_journals.source_journal_service import SourceJournalService

source_journal_cli = typer.Typer()


@source_journal_cli.command()
def check_all_journal_links():
    """
    Check and link journal identifiers for source journals.
    """

    @with_app_lifecycle
    async def _check_all_journal_links():
        source_journal_service = SourceJournalService()
        journal_service = JournalService()
        uids = await source_journal_service.get_source_journal_uids()
        shuffle(uids)
        for uid in uids:
            try:
                journals = await journal_service.link_journal_identifiers(None, uid)
                typer.echo(f"Link to journal checked for source journal {uid}: {journals}")
            except Exception as e: # pylint: disable=broad-except
                typer.echo(f"Error linking journal for source journal {uid}: {e}")

    asyncio.run(_check_all_journal_links())

@source_journal_cli.command()
def check_journal_links(
    uid: str = typer.Argument(..., help="The UID of the source_journal")
):
    """
    Check and link journal identifiers for a specific source journal.
    :param uid: str
        The UID of the source journal to check.
    :return:
    """
    @with_app_lifecycle
    async def _check_journal_links(uid: str):
        journal_service = JournalService()
        try:
            journals = await journal_service.link_journal_identifiers(None, uid)
            typer.echo(f"Link to journal checked for source journal {uid}: {journals}")
        except Exception as e: # pylint: disable=broad-except
            typer.echo(f"Error linking journal for source journal {uid}: {e}")

    asyncio.run(_check_journal_links(uid))
