import asyncio
import random

import typer

from app.commands import with_app_lifecycle
from app.services.people.people_service import PeopleService

people_cli = typer.Typer()


@people_cli.command()
def dispatch_event(
        event: str = typer.Argument(...,
                                    help="The event to dispatch: created, updated, or unchanged"),
        uid: str = typer.Argument(..., help="The UID of the person")
):
    """
    Dispatch a specific event for a person.
    :param event: The event to dispatch (created, updated, unchanged)
    :param uid: The UID of the person
    """
    if event not in {"created", "updated", "unchanged", "deleted"}:
        typer.echo(f"Unsupported event: {event}")
        return

    @with_app_lifecycle
    async def _dispatch_event(event: str, uid: str):
        service = PeopleService()
        if event == "created":
            await service.signal_person_created(uid)
        elif event == "updated":
            await service.signal_person_updated(uid)
        elif event == "unchanged":
            await service.signal_person_unchanged(uid)
        elif event == "deleted":
            await service.signal_person_deleted(uid)
        typer.echo(f"Person event '{event}' dispatched for UID {uid}.")

    asyncio.run(_dispatch_event(event, uid))


@people_cli.command()
def dispatch_all(
        event: str = typer.Argument(...,
                                    help="The event to dispatch: created, updated, or unchanged")
):
    """
    Dispatch a specific event for all people.
    :param event: The event to dispatch (created, updated, unchanged)
    """
    if event not in {"created", "updated", "unchanged"}:
        typer.echo(f"Unsupported event: {event}")
        return

    @with_app_lifecycle
    async def _dispatch_all(event: str):
        service = PeopleService()
        try:
            uids = await service.get_all_person_uids(external=False)
            random.shuffle(uids)
            for uid in uids:
                try:
                    if event == "created":
                        await service.signal_person_created(uid)
                    elif event == "updated":
                        await service.signal_person_updated(uid)
                    elif event == "unchanged":
                        await service.signal_person_unchanged(uid)
                    typer.echo(f"Event '{event}' dispatched for UID {uid}.")
                # pylint: disable=broad-except
                except Exception as e:
                    typer.echo(f"Error dispatching event for UID {uid}: {e}")
        # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Failed to dispatch events for all people: {e}")

    asyncio.run(_dispatch_all(event))


@people_cli.command()
def fetch_publications(
        uid: str = typer.Argument(..., help="The UID of the person"),
        harvesters: str = typer.Option(
            None,
            "--harvesters",
            "-h",
            help="Comma-separated list of harvesters to use for fetching publications. "
                 "If not provided, all configured harvesters will be used."
        )
):
    """
    Fetch publications for a person.
    :param uid: The UID of the person
    :param harvesters: Comma-separated list of harvesters to use for fetching publications.
                       If not provided, all configured harvesters will be used.
    """

    @with_app_lifecycle
    async def _fetch_publications(uid: str):
        service = PeopleService()
        if harvesters:
            harvesters_list = [h.strip() for h in harvesters.split(",")]
            if not harvesters_list:
                typer.echo("No valid harvesters provided.")
                return
        await service.signal_publications_to_be_updated(uid, harvesters)
        typer.echo(f"Publications fetched for person {uid}.")

    asyncio.run(_fetch_publications(uid))

@people_cli.command()
def fetch_publication_random(
):
    """
    Fetch publications for a random person.
    """

    @with_app_lifecycle
    async def _fetch_publication_random():
        service = PeopleService()
        try:
            uids = await service.get_all_person_uids(external=False)
            uid = random.choice(uids)
            await service.signal_publications_to_be_updated(uid)
            typer.echo(f"Publications fetched for person {uid}.")
        # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Failed to fetch publications for a random person: {e}")

    asyncio.run(_fetch_publication_random())

@people_cli.command()
def fetch_publications_all():
    """
    Fetch publications for all people.
    """

    @with_app_lifecycle
    async def _fetch_publications_all():
        service = PeopleService()
        try:
            uids = await service.get_all_person_uids(external=False)
            random.shuffle(uids)
            for uid in uids:
                try:
                    await service.signal_publications_to_be_updated(uid)
                    typer.echo(f"Publications fetched for person {uid}.")
                # pylint: disable=broad-except
                except Exception as e:
                    typer.echo(f"Error fetching publications for person {uid}: {e}")
        # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Failed to fetch publications for all people: {e}")

    asyncio.run(_fetch_publications_all())


@people_cli.command()
def resave_people_all():
    """
    Reads all people from the database and saves them again.

    """

    @with_app_lifecycle
    async def _resave_people_all():
        service = PeopleService()
        uids = await service.get_all_person_uids(external=False)
        random.shuffle(uids)
        for uid in uids:
            person = await service.get_person(uid)
            await service.update_person(person)
            typer.echo(f"Person {uid} resaved.")

    asyncio.run(_resave_people_all())


@people_cli.command()
def resave_person(
        uid: str = typer.Argument(..., help="The UID of the person")
):
    """
    Reads a person from the database and saves it again.

    """

    @with_app_lifecycle
    async def _resave_person(uid: str):
        service = PeopleService()
        person = await service.get_person(uid)
        await service.update_person(person)
        typer.echo(f"Person {uid} resaved.")

    asyncio.run(_resave_person(uid))
