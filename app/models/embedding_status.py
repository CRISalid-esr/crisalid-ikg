from enum import Enum


class EmbeddingStatus(str, Enum):
    """Embedding computation lifecycle status for Embeddable nodes."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
