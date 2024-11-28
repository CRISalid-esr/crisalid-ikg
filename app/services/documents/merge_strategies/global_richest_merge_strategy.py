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
        self.textual_document = self.document_type(uid=self.textual_document_uid)
        self._add_titles()
        self._add_abstracts()
        self._add_subjects()
        return self.textual_document

    def _score(self, record: SourceRecord) -> int:
        return (
                self.parameters.get("titles", 0) *
                len("".join([title.value for title in record.titles])) +
                self.parameters.get("abstracts", 0) *
                len("".join([abstract.value for abstract in record.abstracts])) +
                self.parameters.get("contributions", 0) * len(record.contributions or []) +
                self.parameters.get("subjects", 0) * len(record.subjects or [])
        )

    def _add_titles(self):
        self.textual_document.titles = self._first_non_empty_field("titles")

    def _add_abstracts(self):
        self.textual_document.abstracts = self._first_non_empty_field("abstracts")

    def _add_subjects(self):
        self.textual_document.subjects = self._first_non_empty_field("subjects")

    def _first_non_empty_field(self, field_name: str):
        return next((getattr(record, field_name) for record in self.source_records if
                     getattr(record, field_name)), [])
