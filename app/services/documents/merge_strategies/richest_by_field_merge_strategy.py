from typing import Generic, TypeVar

from app.models.textual_document import TextualDocument
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class RichestByFieldMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on the richness of metadata by field
    """

    def merge(self) -> TextualDocument:
        return TextualDocument()
