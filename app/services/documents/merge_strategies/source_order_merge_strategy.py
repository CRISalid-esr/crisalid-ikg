from typing import TypeVar, Generic

from app.models.document import Document
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class SourceOrderMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on harvester order
    """

    def merge(self) -> Document:
        return self.document_type()
