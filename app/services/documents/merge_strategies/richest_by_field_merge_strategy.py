from typing import Generic, TypeVar

from app.models.source_records import SourceRecord
from app.models.textual_document import TextualDocument
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")

class RichestByFieldMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on the richness of metadata
    """

    def merge(self) -> TextualDocument:
        # Calculate scores for each record
        def score(record: SourceRecord) -> int:
            return (
                self.parameters.get("title", 0) * len(record.title or "") +
                self.parameters.get("abstract", 0) * len(record.abstract or "") +
                self.parameters.get("authors", 0) * len(record.authors or []) +
                self.parameters.get("keywords", 0) * len(record.keywords or [])
            )

        # Find the record with the highest score
        best_record = max(self.source_records, key=score, default=None)

        # Create a TextualDocument from the best record
        if best_record:
            return TextualDocument.from_source_record(best_record)
        return TextualDocument()
