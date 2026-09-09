from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for embedding computation providers."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Compute embeddings for a list of texts.

        :param texts: list of text strings to embed
        :return: list of embedding vectors in the same order as the input
        """
