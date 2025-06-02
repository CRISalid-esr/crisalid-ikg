import asyncio

import typer

from app.commands import with_app_lifecycle
from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.person_dao import PersonDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.people import Person
from app.models.source_records import SourceRecord

source_record_cli = typer.Typer()


@source_record_cli.command()
def resave_source_records_all():
    """
    Reads all source_records from the database and saves them again.

    """

    @with_app_lifecycle
    async def _resave_source_records_all():
        settings = get_app_settings()
        factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
        source_record_dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        person_dao: PersonDAO = factory.get_dao(Person)
        uids = await source_record_dao.get_all_uids()
        for uid in uids:
            source_record = await source_record_dao.get(uid)
            first_person_uid = source_record.harvested_for_uids[0]
            first_person = await person_dao.get(first_person_uid)
            await source_record_dao.update(source_record, first_person)
            typer.echo(f"Source record {uid} resaved with first person {first_person_uid}.")

    asyncio.run(_resave_source_records_all())


@source_record_cli.command()
def resave_source_record(
        uid: str = typer.Argument(..., help="The UID of the source_record")
):
    """
    Reads a source_record from the database and saves it again.

    """

    @with_app_lifecycle
    async def _resave_source_record(uid: str):
        settings = get_app_settings()
        factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
        source_record_dao: SourceRecordDAO = factory.get_dao(SourceRecord)
        person_dao: PersonDAO = factory.get_dao(Person)
        source_record = await source_record_dao.get(uid)
        first_person_uid = source_record.harvested_for_uids[0]
        first_person = await person_dao.get(first_person_uid)
        await source_record_dao.update(source_record, first_person)
        typer.echo(f"Source record {uid} resaved.")

    asyncio.run(_resave_source_record(uid))
