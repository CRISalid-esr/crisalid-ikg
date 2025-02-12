from typing import Generic, TypeVar

from app.models.source_records import SourceRecord
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class GlobalRichestMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on the richness of metadata
    """

    def merge(self) -> T:
        self.source_records = sorted(self.source_records, key=self._score, reverse=True)
        self.document = self.document_type()
        self._add_titles()
        self._add_abstracts()
        self._add_subjects()
        self._add_publication_date()
        return self.document

    def _score(self, record: SourceRecord) -> int:
        return (
                self.parameters.get("titles", 0) *
                len("".join([title.value for title in record.titles])) +
                self.parameters.get("abstracts", 0) *
                len("".join([abstract.value for abstract in record.abstracts])) +
                self.parameters.get("contributions", 0) * len(record.contributions or []) +
                self.parameters.get("subjects", 0) * len(record.subjects or []) +
                self.parameters.get("issued", 0) * (1 if record.raw_issued else 0)
        )

    def _add_titles(self):
        self.document.titles = self._first_non_empty_field("titles")

    def _add_abstracts(self):
        self.document.abstracts = self._first_non_empty_field("abstracts")

    def _add_subjects(self):
        self.document.subjects = self._first_non_empty_field("subjects")

    def _add_publication_date(self):
        self.document.publication_date = next(
            (record.raw_issued for record in self.source_records if record.raw_issued),
            None
        )

    def _first_non_empty_field(self, field_name: str):
        return next((getattr(record, field_name) for record in self.source_records if
                     getattr(record, field_name)), [])
