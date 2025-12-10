import asyncio
import random

import typer

from app.commands import with_app_lifecycle
from app.services.documents.document_service import DocumentService

document_cli = typer.Typer()


async def handle_event(uid: str, event: str, service: DocumentService):
    """
    Handle dispatching a specific event for a given document UID.
    """
    if event == "updated":
        await service.signal_document_updated(uid)
    elif event == "created":
        await service.signal_document_created(uid)
    elif event == "deleted":
        await service.signal_document_deleted(uid)
    elif event == "unchanged":
        await service.signal_document_unchanged(uid)
    else:
        raise ValueError(f"Unsupported event: {event}")


async def handle_all_events(event: str, service: DocumentService):
    """
    Handle dispatching a specific event for all document UIDs.
    """
    uids = await service.get_document_uids()
    random.shuffle(uids)
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
    Recompute metadata for a document and trigger updated event
    """

    @with_app_lifecycle
    async def _recompute_metadata(uid: str):
        service = DocumentService()
        await service.update_from_source_records(None, uid)
        typer.echo(f"Metadata recomputation for document {uid} completed.")

    asyncio.run(_recompute_metadata(uid))

@document_cli.command()
def recompute_metadata_random(
):
    """
    Fetch publications for a random person.
    """

    @with_app_lifecycle
    async def _recompute_metadata_random():
        service = DocumentService()
        try:
            uids = await service.get_document_uids()
            uid = random.choice(uids)
            await service.update_from_source_records(None, uid)
            typer.echo(f"Metadata recomputation for document {uid} completed.")
        # pylint: disable=broad-except
        except Exception as e:
            typer.echo(f"Error recomputing metadata for document {uid}: {e}")

    asyncio.run(_recompute_metadata_random())

@document_cli.command()
def recompute_metadata_all():
    """
    Recompute metadata for all documents and trigger updated event
    """

    @with_app_lifecycle
    async def _recompute_metadata_all():
        service = DocumentService()
        uids = await service.get_document_uids()
        # shuffle the list of UIDs to avoid processing in the same order
        random.shuffle(uids)
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
    Dispatch an event for a specific document.
    """
    if event not in {"updated", "created", "deleted", "unchanged"}:
        typer.echo(f"Event {event} is not supported.")
        return

    @with_app_lifecycle
    async def _dispatch_event(event: str, uid: str):
        service = DocumentService()
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
    Dispatch an event for all documents.
    """
    if event not in {"updated", "created", "deleted", "unchanged"}:
        typer.echo(f"Event {event} is not supported.")
        return

    @with_app_lifecycle
    async def _dispatch_all(event: str):
        service = DocumentService()
        await handle_all_events(event, service)
        typer.echo(f"All document events of type '{event}' dispatched successfully.")

    asyncio.run(_dispatch_all(event))
