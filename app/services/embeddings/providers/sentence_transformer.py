from app.services.embeddings.providers.base import EmbeddingProvider


class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence-transformers embedding provider (not yet implemented)."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("SentenceTransformerProvider is not yet implemented")
