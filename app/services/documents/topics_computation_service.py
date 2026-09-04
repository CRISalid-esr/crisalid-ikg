"""
Compute Document -> Topic links with Crisalid-taxi.
"""
from dataclasses import dataclass, field

from loguru import logger

from app.config import get_app_settings
from app.models.document import Document
from app.models.literal import Literal
from app.services.documents.crisalid_taxi_client import CrisalidTaxiClient, TaxiMatch
from app.services.documents.topics_input_builder import build_topics_input, TopicsInput

TOPIC_REL_TYPE = "HAS_TOPIC"


@dataclass
class TopicsResult:
    """Topics to write for one document after a successful Crisalid-taxi call."""

    document_uid: str
    input_hash: str
    model: str
    topics: list[tuple[str, float]]  # (concept uid, score) sorted by score desc

    def as_row(self) -> dict:
        """
        :return: the parameters expected by the sync_document_crisalid_topics queries
        """
        return {
            "document_uid": self.document_uid,
            "input_hash": self.input_hash,
            "model": self.model,
            "topics": [{"uid": uid, "score": score} for uid, score in self.topics],
        }


@dataclass
class DocumentTopicsRow:
    """Read model of a document for batch topics computation (see DocumentDAO)."""

    uid: str
    titles: list[Literal]
    abstracts: list[Literal]
    subject_pref_labels: list[Literal]
    topics_input_hash: str | None = None


@dataclass
class TopicsBatchStats:
    """Counters of a batch computation."""

    skipped_no_input: int = 0
    skipped_unchanged: int = 0
    failed: int = 0
    computed: int = 0
    missing_topics: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (f"computed={self.computed} skipped_unchanged={self.skipped_unchanged} "
                f"skipped_no_input={self.skipped_no_input} failed={self.failed}")


class TopicsComputationService:
    """
    Builds the Crisalid-taxi input for documents, calls the service and filters the matches.
    Every early return is a skip: nothing is written and existing links are kept.
    """

    def __init__(self):
        self.settings = get_app_settings()

    async def compute_topics_for_document(
            self, document_uid: str, document: Document,
            previous_hash: str | None, force: bool = False) -> TopicsResult | None:
        """
        Compute the Crisalid-taxi topics of a single document.

        :param document_uid: the document uid (used as Crisalid-taxi input id)
        :param document: the (possibly not yet persisted) document
        :param previous_hash: ``topics_input_hash`` stored on the document node, if any
        :param force: call Crisalid-taxi even when the input hash is unchanged
        :return: a TopicsResult to persist, or None when nothing should be written
        """
        if not self.settings.taxi_enabled:
            return None
        try:
            topics_input = self._build_input(document.titles, document.abstracts,
                                             [label for subject in document.subjects
                                              for label in subject.pref_labels])
            if topics_input is None:
                logger.debug("No usable Crisalid-taxi input for document {}", document_uid)
                return None
            if not force and topics_input.input_hash == previous_hash:
                logger.debug("Topics input unchanged for document {}", document_uid)
                return None
            response = await CrisalidTaxiClient().match(
                [{"id": document_uid, "text": topics_input.text}])
            if response is None:
                return None
            result = TopicsResult(
                document_uid=document_uid,
                input_hash=topics_input.input_hash,
                model=response.model,
                topics=self._filter(response.results.get(document_uid, [])),
            )
            return result
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error while computing Crisalid-taxi topics for document {}",
                             document_uid)
            return None

    async def compute_topics_batch(
            self, rows: list[DocumentTopicsRow], force: bool = False
    ) -> tuple[list[TopicsResult], TopicsBatchStats]:
        """
        Compute the Crisalid-taxi topics of several documents with a single request.

        :param rows: documents to process (at most ``taxi_batch_size`` per call is advised)
        :param force: call Crisalid-taxi even when the input hash is unchanged
        :return: the results to persist and the counters of the batch
        """
        stats = TopicsBatchStats()
        inputs: dict[str, TopicsInput] = {}
        for row in rows:
            topics_input = self._build_input(row.titles, row.abstracts, row.subject_pref_labels)
            if topics_input is None:
                stats.skipped_no_input += 1
                continue
            if not force and topics_input.input_hash == row.topics_input_hash:
                stats.skipped_unchanged += 1
                continue
            inputs[row.uid] = topics_input
        if not inputs:
            return [], stats
        response = await CrisalidTaxiClient().match(
            [{"id": uid, "text": topics_input.text} for uid, topics_input in inputs.items()])
        if response is None:
            stats.failed += len(inputs)
            return [], stats
        results = [
            TopicsResult(
                document_uid=uid,
                input_hash=topics_input.input_hash,
                model=response.model,
                topics=self._filter(response.results.get(uid, [])),
            )
            for uid, topics_input in inputs.items()
        ]
        stats.computed += len(results)
        return results, stats

    @staticmethod
    def log_missing_topics(result: TopicsResult, linked_uids: list[str]) -> list[str]:
        """
        Log a warning for every topic requested by Crisalid-taxi but absent from the graph.

        :param result: the result that was written
        :param linked_uids: the topic uids actually linked by the DAO
        :return: the missing topic uids
        """
        missing = [uid for uid, _ in result.topics if uid not in set(linked_uids)]
        for uid in missing:
            logger.warning("Topic {} returned by Crisalid-taxi not found in graph "
                           "(document {}) — skipped", uid, result.document_uid)
        return missing

    def _build_input(self, titles, abstracts, pref_labels) -> TopicsInput | None:
        return build_topics_input(
            titles=titles,
            abstracts=abstracts,
            pref_labels=pref_labels,
            languages=self.settings.taxi_languages,
            min_input_length=self.settings.taxi_min_input_length,
        )

    def _filter(self, matches: list[TaxiMatch]) -> list[tuple[str, float]]:
        threshold = self.settings.taxi_similarity_threshold
        kept = [(match.concept_uid, match.value) for match in matches
                if match.rel_type == TOPIC_REL_TYPE and match.value >= threshold]
        kept.sort(key=lambda item: item[1], reverse=True)
        return kept[: self.settings.taxi_max_topics]
