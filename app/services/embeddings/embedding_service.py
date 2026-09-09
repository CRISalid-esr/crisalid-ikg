import hashlib

from loguru import logger

from app.config import get_app_settings
from app.graph.neo4j.embeddable_dao import EmbeddableDAO
from app.services.embeddings.providers.base import EmbeddingProvider
from app.services.embeddings.providers.factory import get_embedding_provider


class EmbeddingService:
    """
    Service responsible for computing and storing embeddings on Embeddable nodes.

    Can be used as a signal handler (on_literals_pending) or invoked directly
    from the CLI bulk command.
    """

    def __init__(self):
        self.settings = get_app_settings()
        self.dao = EmbeddableDAO()

    async def on_literals_pending(self, _) -> None:
        """
        Signal handler for literal_updated: process all pending Embeddable nodes.
        No-op when embedding_enabled is False.
        """
        if not self.settings.embedding_enabled:
            return
        try:
            await self._process_pending(statuses=["pending"])
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Embedding processing failed: {}", e)

    async def compute_embeddings(
        self,
        statuses: list[str],
        types: list[str] | None = None,
        model_exclude: str | None = None,
    ) -> None:
        """
        Bulk embedding computation entry point used by the CLI.

        :param statuses: embedding_status values to process (e.g. ['pending', 'failed'])
        :param types: optional list of literal types to restrict processing to
        :param model_exclude: if set, skip nodes already embedded with this model
        """
        provider = get_embedding_provider(self.settings)
        skip = 0
        batch_size = self.settings.embedding_batch_size
        total_processed = 0

        while True:
            nodes = await self.dao.get_pending_nodes(
                statuses=statuses,
                types=types,
                model_exclude=model_exclude,
                skip=skip,
                batch_size=batch_size,
            )
            if not nodes:
                break

            await self._embed_batch(nodes, provider)
            total_processed += len(nodes)
            skip += batch_size
            logger.info("Embedded {} nodes so far...", total_processed)

        logger.info("Embedding complete. Total nodes processed: {}", total_processed)

    async def _process_pending(self, statuses: list[str]) -> None:
        provider = get_embedding_provider(self.settings)
        skip = 0
        batch_size = self.settings.embedding_batch_size

        while True:
            nodes = await self.dao.get_pending_nodes(
                statuses=statuses,
                skip=skip,
                batch_size=batch_size,
            )
            if not nodes:
                break
            await self._embed_batch(nodes, provider)
            skip += batch_size

    async def _embed_batch(self, nodes: list[dict], provider: EmbeddingProvider) -> None:
        to_embed = []
        already_valid = []

        for node in nodes:
            current_hash = hashlib.sha256(node["value"].encode("utf-8")).hexdigest()
            node_model = node.get("embedding_model")
            node_hash = node.get("embedding_hash")
            node_embedding = node.get("embedding")

            if (
                node_embedding is not None
                and node_hash == current_hash
                and node_model == self.settings.embedding_api_model
            ):
                already_valid.append(
                    {
                        "element_id": node["element_id"],
                        "embedding": node_embedding,
                        "embedding_hash": current_hash,
                        "embedding_model": node_model,
                    }
                )
            else:
                to_embed.append((node, current_hash))

        if already_valid:
            await self.dao.update_embeddings_batch(already_valid)

        if not to_embed:
            return

        texts = [n["value"] for n, _ in to_embed]
        try:
            vectors = await provider.embed_texts(texts)
        # pylint: disable=broad-except
        except Exception as e:
            logger.error("Embedding API call failed for batch of {} nodes: {}", len(to_embed), e)
            for node, _ in to_embed:
                await self.dao.mark_failed(node["element_id"], str(e))
            return

        rows = [
            {
                "element_id": node["element_id"],
                "embedding": vector,
                "embedding_hash": current_hash,
                "embedding_model": self.settings.embedding_api_model,
            }
            for (node, current_hash), vector in zip(to_embed, vectors)
        ]
        await self.dao.update_embeddings_batch(rows)
