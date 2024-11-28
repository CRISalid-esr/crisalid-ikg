from typing import TypeVar, Generic

from app.models.textual_document import TextualDocument
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class SourceOrderMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on harvester order
    """

    def merge(self) -> TextualDocument:
        harvesters_order = self.parameters.get("harvesters", [])

        sorted_records = sorted(
            self.source_records,
            key=lambda record: harvesters_order.index(
                record.harvester) if record.harvester in harvesters_order else float('inf')
        )

        if sorted_records:
            return TextualDocument.from_source_record(sorted_records[0])
        return TextualDocument()
