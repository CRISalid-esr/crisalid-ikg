import asyncio
import random
from typing import Optional

import typer

from app.amqp.message_mode import MessageMode
from app.commands import with_app_lifecycle
from app.config import get_app_settings
from app.services.documents.document_service import DocumentService
from app.signals import document_updated

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
def recompute_person_metadata(uid: str = typer.Argument(...,
                            help="The UID of the person whose document are to be recomputed")):
    """
    Recompute metadata for all documents linked to a person and trigger updated event
    """

    @with_app_lifecycle
    async def _recompute_person_metadata(uid: str):
        doc_service = DocumentService()
        doc_uids = await doc_service.get_document_uids_of_person(uid)

        if not doc_uids:
            typer.echo(f"No documents linked to person {uid} were found.")
        for doc_uid in doc_uids:
            await doc_service.update_from_source_records(None, doc_uid)
            typer.echo(f"Metadata recomputation for document {doc_uid} completed.")

    asyncio.run(_recompute_person_metadata(uid))

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


def _require_taxi_enabled() -> None:
    if not get_app_settings().taxi_enabled:
        typer.echo("ERROR: Crisalid-taxi is disabled. Set TAXI_ENABLED=true to proceed.",
                   err=True)
        raise typer.Exit(code=1)


async def _dispatch_topics_updates(written: list[dict], results_by_uid: dict,
                                   dispatch: bool) -> int:
    """
    Emit document_updated for the documents whose crisalid topics changed.
    :return: number of events emitted
    """
    if not dispatch:
        return 0
    emitted = 0
    for row in written:
        if row["document_uid"] not in results_by_uid:
            continue
        if set(row["previous_uids"]) != set(row["linked_uids"]):
            await document_updated.send_async(None, document_uid=row["document_uid"],
                                              mode=MessageMode.BATCH)
            emitted += 1
    return emitted


@document_cli.command()
def recompute_topics(
        uid: str = typer.Argument(..., help="The UID of the document"),
        no_dispatch: bool = typer.Option(False, "--no-dispatch",
                                         help="Do not emit a document_updated event"),
):
    """
    Recompute the Crisalid-taxi topics of a single document (the input hash is ignored).

    Requires TAXI_ENABLED=true in the environment.
    """

    @with_app_lifecycle
    async def _recompute_topics():
        # pylint: disable=import-outside-toplevel
        from app.services.documents.topics_computation_service import TopicsComputationService

        _require_taxi_enabled()
        service = DocumentService()
        document = await service.get_document(uid)
        if document is None:
            typer.echo(f"Document {uid} not found.", err=True)
            raise typer.Exit(code=1)
        topics_service = TopicsComputationService()
        result = await topics_service.compute_topics_for_document(
            uid, document, previous_hash=None, force=True)
        if result is None:
            typer.echo(f"No topics computed for document {uid} "
                       "(input too short, no usable language or Crisalid-taxi unavailable).")
            return
        written = await service.write_crisalid_topics(result)
        if written is None:
            typer.echo(f"Document {uid} could not be updated.", err=True)
            raise typer.Exit(code=1)
        for topic_uid, score in result.topics:
            status = "linked" if topic_uid in written["linked_uids"] else "NOT FOUND"
            typer.echo(f"  {topic_uid}  {score:.4f}  {status}")
        emitted = await _dispatch_topics_updates([written], {uid: result}, not no_dispatch)
        typer.echo(f"Topics recomputation for document {uid} completed "
                   f"({len(written['linked_uids'])} topics, model {result.model}, "
                   f"{emitted} event emitted).")

    asyncio.run(_recompute_topics())


@document_cli.command()
def recompute_topics_all(
        missing_only: bool = typer.Option(
            False, "--missing-only",
            help="Only documents that never got Crisalid-taxi topics."),
        force: bool = typer.Option(
            False, "--force",
            help="Ignore the stored input hash (use after a Crisalid-taxi model change)."),
        batch_size: Optional[int] = typer.Option(
            None, "--batch-size",
            help="Documents per Crisalid-taxi request (default TAXI_BATCH_SIZE)."),
        no_dispatch: bool = typer.Option(
            False, "--no-dispatch", help="Do not emit document_updated events."),
):
    """
    Recompute the Crisalid-taxi topics of all documents, in batches.

    Without --force, documents whose title, abstract and subjects are unchanged
    are skipped without calling Crisalid-taxi. Requires TAXI_ENABLED=true.
    """

    @with_app_lifecycle
    async def _recompute_topics_all():
        # pylint: disable=import-outside-toplevel
        from app.services.documents.crisalid_taxi_client import CrisalidTaxiClient
        from app.services.documents.topics_computation_service import TopicsComputationService

        _require_taxi_enabled()
        settings = get_app_settings()
        page_size = batch_size or settings.taxi_batch_size
        service = DocumentService()
        topics_service = TopicsComputationService()
        typer.echo(f"Topics state before: {await service.count_topics_state()}")
        typer.echo(f"Processing missing_only={missing_only} force={force} "
                   f"batch_size={page_size} dispatch={not no_dispatch}")
        skip = 0
        totals = {"computed": 0, "skipped_unchanged": 0, "skipped_no_input": 0,
                  "failed": 0, "events": 0, "missing_topics": 0}
        while True:
            rows = await service.get_documents_for_topics_computation(
                skip=skip, limit=page_size, missing_only=missing_only)
            if not rows:
                break
            results, stats = await topics_service.compute_topics_batch(rows, force=force)
            written = await service.write_crisalid_topics_batch(results)
            results_by_uid = {result.document_uid: result for result in results}
            for row in written:
                totals["missing_topics"] += len(TopicsComputationService.log_missing_topics(
                    results_by_uid[row["document_uid"]], row["linked_uids"]))
            totals["events"] += await _dispatch_topics_updates(
                written, results_by_uid, not no_dispatch)
            for key in ("computed", "skipped_unchanged", "skipped_no_input", "failed"):
                totals[key] += getattr(stats, key)
            typer.echo(f"Page skip={skip}: {stats} (cumulative: {totals})")
            if CrisalidTaxiClient.is_open():
                typer.echo("Crisalid-taxi circuit open — stopping; rerun later or raise "
                           "TAXI_MAX_CONSECUTIVE_FAILURES.", err=True)
                raise typer.Exit(code=2)
            # with --missing-only, processed documents leave the result set: stay on page 0
            # unless nothing was written (skipped documents would otherwise loop forever)
            if not missing_only or not written:
                skip += page_size
        typer.echo(f"Done. {totals}")
        typer.echo(f"Topics state after: {await service.count_topics_state()}")

    asyncio.run(_recompute_topics_all())
