import asyncio
from typing import Optional

import typer

from app.commands import with_app_lifecycle
from app.config import get_app_settings

literal_cli = typer.Typer()


@literal_cli.command()
def compute_embeddings(
    types: Optional[str] = typer.Option(
        None,
        help=(
            "Comma-separated list of literal types to process. "
            "Only Embeddable nodes are processed; this further restricts which types."
        ),
    ),
    new_model: Optional[str] = typer.Option(
        None,
        help="Only process Embeddable nodes whose embeddings were not computed with this model.",
    ),
    statuses: str = typer.Option(
        "pending,failed",
        help="Comma-separated list of embedding_status values to process.",
    ),
    recreate_vector_indexes: bool = typer.Option(
        False,
        help="Reset all embedding properties, drop and recreate the vector index, "
             "then recompute all embeddings. Incompatible with --statuses.",
    ),
):
    """
    Compute or recompute embeddings for Embeddable (Literal / TextLiteral) nodes.

    Requires ENABLE_EMBEDDINGS=true in the environment.
    """
    @with_app_lifecycle
    async def _run():
        # pylint: disable=import-outside-toplevel
        from app.graph.neo4j.embeddable_dao import EmbeddableDAO
        from app.services.embeddings.embedding_service import EmbeddingService

        settings = get_app_settings()

        if not settings.embedding_enabled:
            typer.echo(
                "ERROR: Embeddings are disabled. Set ENABLE_EMBEDDINGS=true to proceed.",
                err=True,
            )
            raise typer.Exit(code=1)

        dao = EmbeddableDAO()
        service = EmbeddingService()

        if recreate_vector_indexes:
            typer.echo("Resetting all embedding properties on Embeddable nodes...")
            await dao.reset_all_for_migration()
            typer.echo("Dropping existing vector index...")
            await dao.drop_vector_index()
            typer.echo(
            f"Recreating vector index with {settings.embedding_dimensions} dimensions..."
        )
            await dao.recreate_vector_index(settings.embedding_dimensions)
            effective_statuses = ["pending"]
        else:
            effective_statuses = [s.strip() for s in statuses.split(",")]

        parsed_types = [t.strip() for t in types.split(",")] if types else None

        counts = await dao.count_by_status()
        typer.echo(f"Embedding status counts: {counts}")
        typer.echo(
            f"Processing statuses={effective_statuses}, types={parsed_types}, "
            f"model_exclude={new_model}"
        )

        await service.compute_embeddings(
            statuses=effective_statuses,
            types=parsed_types,
            model_exclude=new_model,
        )

        counts_after = await dao.count_by_status()
        typer.echo(f"Done. Embedding status counts after: {counts_after}")

    asyncio.run(_run())
