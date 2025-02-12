from typing import Generic, TypeVar

from app.models.document import Document
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class RichestByFieldMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on the richness of metadata by field
    """

    def merge(self) -> Document:
        return self.document_type()
