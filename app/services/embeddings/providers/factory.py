from app.services.embeddings.providers.base import EmbeddingProvider
from app.services.embeddings.providers.openai_compatible import OpenAICompatibleProvider
from app.services.embeddings.providers.sentence_transformer import SentenceTransformerProvider


def get_embedding_provider(settings) -> EmbeddingProvider:
    """Instantiate the embedding provider configured in settings."""
    if settings.embedding_provider == "openai_compatible":
        return OpenAICompatibleProvider(settings)
    if settings.embedding_provider == "sentence_transformer":
        return SentenceTransformerProvider(settings)
    raise ValueError(
        f"Unknown embedding provider: '{settings.embedding_provider}'. "
        "Supported values: openai_compatible, sentence_transformer"
    )
