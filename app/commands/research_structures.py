import asyncio
import typer
from app.commands import with_app_lifecycle
from app.services.organizations.research_structure_service import ResearchStructureService

research_structure_cli = typer.Typer()

@research_structure_cli.command()
def dispatch_event(
    event: str = typer.Argument(..., help="The event to dispatch: created, updated, or unchanged"),
    uid: str = typer.Argument(..., help="The UID of the research structure")
):
    """
    Dispatch a specific event for a research structure.
    :param event: The event to dispatch (created, updated, unchanged)
    :param uid: The UID of the research structure
    """
    if event not in {"created", "updated", "unchanged", "deleted"}:
        typer.echo(f"Unsupported event: {event}")
        return

    @with_app_lifecycle
    async def _dispatch_event(event: str, uid: str):
        service = ResearchStructureService()
        if event == "created":
            await service.signal_research_unit_created(uid)
        elif event == "updated":
            await service.signal_research_unit_updated(uid)
        elif event == "unchanged":
            await service.signal_research_unit_unchanged(uid)
        elif event == "deleted":
            await service.signal_research_unit_deleted(uid)
        typer.echo(f"Research structure event '{event}' dispatched for UID {uid}.")

    asyncio.run(_dispatch_event(event, uid))


@research_structure_cli.command()
def dispatch_all(
    event: str = typer.Argument(..., help="The event to dispatch: created, updated, or unchanged")
):
    """
    Dispatch a specific event for all research structures.
    :param event: The event to dispatch (created, updated, unchanged)
    """
    if event not in {"created", "updated", "unchanged"}:
        typer.echo(f"Unsupported event: {event}")
        return

    @with_app_lifecycle
    async def _dispatch_all(event: str):
        service = ResearchStructureService()
        try:
            uids = await service.get_all_structure_uids()
            for uid in uids:
                try:
                    if event == "created":
                        await service.signal_research_unit_created(uid)
                    elif event == "updated":
                        await service.signal_research_unit_updated(uid)
                    elif event == "unchanged":
                        await service.signal_research_unit_unchanged(uid)
                    typer.echo(f"Event '{event}' dispatched for UID {uid}.")
                # pylint: disable=broad-except
                except Exception as e:
                    typer.echo(f"Error dispatching event for UID {uid}: {e}")
        # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Failed to dispatch events for all research structures: {e}")

    asyncio.run(_dispatch_all(event))
