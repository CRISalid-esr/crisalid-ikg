# pylint: disable=duplicate-code
from loguru import logger
from neo4j.exceptions import DatabaseError

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.utils import load_query


class EmbeddableDAO:
    """
    Data access object for Embeddable nodes (Literal:Embeddable and TextLiteral:Embeddable).
    Handles all embedding-related read/write operations. Not registered in the DAO factory.
    """

    @handle_database_errors
    async def get_pending_nodes(  # pylint: disable=too-many-arguments
        self,
        statuses: list[str],
        types: list[str] | None = None,
        model_exclude: str | None = None,
        skip: int = 0,
        batch_size: int = 64,
    ) -> list[dict]:
        """
        Fetch Embeddable nodes matching the given statuses, optionally filtered by type
        and excluding nodes already embedded with a specific model.
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("get_pending_embeddable_nodes"),
                        statuses=statuses,
                        types=types,
                        model_exclude=model_exclude,
                        skip=skip,
                        batch_size=batch_size,
                    )
                    return [
                        {
                            "element_id": record["element_id"],
                            "value": record["value"],
                            "type": record["type"],
                        }
                        async for record in result
                    ]

    @handle_database_errors
    async def update_embeddings_batch(self, rows: list[dict]) -> None:
        """
        Bulk-update embedding properties on a batch of Embeddable nodes.

        Each row must contain: element_id, embedding, embedding_hash, embedding_model.
        """
        if not rows:
            return
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    await tx.run(
                        load_query("update_embeddable_node_embedding"),
                        rows=rows,
                    )

    @handle_database_errors
    async def mark_failed(self, element_id: str, error: str) -> None:
        """Mark an Embeddable node as failed with an error message."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    await tx.run(
                        load_query("mark_embeddable_node_failed"),
                        element_id=element_id,
                        error=error,
                    )

    @handle_database_errors
    async def reset_all_for_migration(self) -> None:
        """
        Reset embedding properties on all Embeddable nodes to prepare for a full
        re-embedding with a new model. Preserves embedding_model and embedding_updated_at
        for audit purposes.
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    await tx.run(load_query("reset_embeddable_nodes_for_migration"))

    @handle_database_errors
    async def count_by_status(self) -> dict[str, int]:
        """Return a dict mapping embedding_status → count for all Embeddable nodes."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(load_query("count_embeddable_nodes_by_status"))
                    return {
                        record["status"]: record["count"]
                        async for record in result
                    }

    async def drop_vector_index(self) -> None:
        """Drop the Embeddable vector index (used before recreating with new dimensions)."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                try:
                    await session.run("DROP INDEX embeddable_embedding IF EXISTS")
                except DatabaseError as e:
                    logger.error("Error dropping Embeddable vector index: {}", e)
                    raise

    async def recreate_vector_index(self, dimensions: int) -> None:
        """Recreate the Embeddable vector index with the given dimension."""
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                try:
                    await session.run(
                        load_query("create_embeddable_vector_index"),
                        dims=dimensions,
                    )
                except DatabaseError as e:
                    logger.error("Error recreating Embeddable vector index: {}", e)
                    raise
