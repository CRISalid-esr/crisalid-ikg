from typing import Generic, TypeVar

from app.models.source_records import SourceRecord
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy

T = TypeVar("T")


class GlobalRichestMergeStrategy(MergeStrategy[T], Generic[T]):
    """
    Merge strategy based on the richness of metadata
    """

    def merge(self) -> T:
        records = self.source_records

        # If a harvester list is provided, exclude all records not in it
        if self.harvesters:
            allowed_harvesters = set(self.harvesters)
            records = [
                record
                for record in records
                if record.harvester.value in allowed_harvesters
            ]

        # Sort by:
        # 1. score descending
        # 2. harvester order ascending (tie-breaker)
        records = sorted(records, key=self._sort_key)

        self.source_records = records
        self.document = self.document_type()
        self._add_titles()
        self._add_abstracts()
        self._add_subjects()
        self._add_publication_date()
        return self.document

    def _sort_key(self, record: SourceRecord):
        return (
            -self._score(record),
            self._harvester_rank(record),
        )

    def _harvester_rank(self, record: SourceRecord) -> int:
        harvester = record.harvester.value
        if self.harvesters and harvester in self.harvesters:
            return self.harvesters.index(harvester)
        return len(self.harvesters)

    def _score(self, record: SourceRecord) -> int:
        title_score = self.parameters.get("titles", 0) * len(
            "".join([title.value for title in record.titles])
        )
        abstract_score = self.parameters.get("abstracts", 0) * len(
            "".join([abstract.value for abstract in record.abstracts])
        )
        contribution_score = self.parameters.get("contributions", 0) * len(
            record.contributions or [])
        subject_score = self.parameters.get("subjects", 0) * len(record.subjects or [])
        issued_score = self.parameters.get("issued", 0) * (1 if record.raw_issued else 0)
        score = title_score + abstract_score + contribution_score + subject_score + issued_score
        return score

    def _add_titles(self):
        self.document.titles = self._first_non_empty_field("titles")

    def _add_abstracts(self):
        self.document.abstracts = self._first_non_empty_field("abstracts")

    def _add_subjects(self):
        # set cant be used because Concept is not hashable
        seen = set()
        unique_subjects = []
        for record in self.source_records:
            for subject in record.subjects:
                identifier = getattr(subject, "uid",
                                     subject)
                if identifier not in seen:
                    seen.add(identifier)
                    unique_subjects.append(subject)

        self.document.subjects = unique_subjects

    def _add_publication_date(self):
        self.document.publication_date = next(
            (record.raw_issued for record in self.source_records if record.raw_issued),
            None
        )

    def _first_non_empty_field(self, field_name: str):
        return next((getattr(record, field_name) for record in self.source_records if
                     getattr(record, field_name)), [])
