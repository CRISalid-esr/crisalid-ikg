import asyncio

import typer

from app.commands import with_app_lifecycle
from app.services.documents.textual_document_service import TextualDocumentService

document_cli = typer.Typer()


async def handle_event(uid: str, event: str, service: TextualDocumentService):
    """
    Handle dispatching a specific event for a given document UID.
    """
    if event == "updated":
        await service.signal_textual_document_updated(uid)
    elif event == "created":
        await service.signal_textual_document_created(uid)
    elif event == "deleted":
        await service.signal_textual_document_deleted(uid)
    elif event == "unchanged":
        await service.signal_textual_document_unchanged(uid)
    else:
        raise ValueError(f"Unsupported event: {event}")


async def handle_all_events(event: str, service: TextualDocumentService):
    """
    Handle dispatching a specific event for all document UIDs.
    """
    uids = await service.get_textual_document_uids()
    for uid in uids:
        try:
            await handle_event(uid, event, service)
            typer.echo(f"Document event '{event}' dispatched for document {uid}.")
            # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Error dispatching event for document {uid}: {e}")


@document_cli.command()
def recompute_metadata(uid: str = typer.Argument(..., help="The UID of the document to recompute")):
    """
    Recompute metadata for a textual document and trigger updated event
    """

    @with_app_lifecycle
    async def _recompute_metadata(uid: str):
        service = TextualDocumentService()
        await service.update_from_source_records(None, uid)
        typer.echo(f"Metadata recomputation for document {uid} completed.")

    asyncio.run(_recompute_metadata(uid))

@document_cli.command()
def recompute_metadata_all():
    """
    Recompute metadata for all textual documents and trigger updated event
    """

    @with_app_lifecycle
    async def _recompute_metadata_all():
        service = TextualDocumentService()
        uids = await service.get_textual_document_uids()
        for uid in uids:
            try:
                await service.update_from_source_records(None, uid)
                typer.echo(f"Metadata recomputation for document {uid} completed.")
                # pylint: disable=broad-except
            except Exception as e:
                typer.echo(f"Error recomputing metadata for document {uid}: {e}")

    asyncio.run(_recompute_metadata_all())


@document_cli.command()
def dispatch_event(
        event: str = typer.Argument(
            ...,
            help="The event to dispatch: created, updated, deleted, or unchanged"),
        uid: str = typer.Argument(..., help="The UID of the document")
):
    """
    Dispatch an event for a specific textual document.
    """
    if event not in {"updated", "created", "deleted", "unchanged"}:
        typer.echo(f"Event {event} is not supported.")
        return

    @with_app_lifecycle
    async def _dispatch_event(event: str, uid: str):
        service = TextualDocumentService()
        await handle_event(uid, event, service)
        typer.echo(f"Document event '{event}' dispatched for document {uid}.")

    asyncio.run(_dispatch_event(event, uid))


@document_cli.command()
def dispatch_all(
        event: str = typer.Argument(
            ...,
            help="The event to dispatch: created, updated, deleted, or unchanged")
):
    """
    Dispatch an event for all textual documents.
    """
    if event not in {"updated", "created", "deleted", "unchanged"}:
        typer.echo(f"Event {event} is not supported.")
        return

    @with_app_lifecycle
    async def _dispatch_all(event: str):
        service = TextualDocumentService()
        await handle_all_events(event, service)
        typer.echo(f"All document events of type '{event}' dispatched successfully.")

    asyncio.run(_dispatch_all(event))
