import asyncio

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
        uid: str = typer.Argument(..., help="The UID of the person")
):
    """
    Fetch publications for a person.
    :param uid: The UID of the person
    """

    @with_app_lifecycle
    async def _fetch_publications(uid: str):
        service = PeopleService()
        await service.signal_publications_to_be_updated(uid)
        typer.echo(f"Publications fetched for person {uid}.")

    asyncio.run(_fetch_publications(uid))


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
