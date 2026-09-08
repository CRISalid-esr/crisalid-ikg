from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.document import Document
from app.models.literal import Literal
from app.models.text_literal import TextLiteral
from app.services.documents.crisalid_taxi_client import TaxiMatch, TaxiMatchResponse
from app.services.documents.topics_computation_service import DocumentTopicsRow, \
    TopicsComputationService

TITLE = Literal(value="Machine learning algorithms for quantum computing", language="en")
ABSTRACT = TextLiteral(value="We study variational circuits on noisy devices.", language="en")


def make_settings(enabled=True, threshold=0.6, max_topics=30, min_length=25,
                  languages=("en", "fr")):
    settings = MagicMock()
    settings.taxi_enabled = enabled
    settings.taxi_similarity_threshold = threshold
    settings.taxi_max_topics = max_topics
    settings.taxi_min_input_length = min_length
    settings.taxi_languages = list(languages)
    return settings


def make_response(matches, ids=("doc-1",), model="bge-m3"):
    return TaxiMatchResponse(model=model, results={doc_id: list(matches) for doc_id in ids})


def topic(uid, value, rel_type="HAS_TOPIC"):
    return TaxiMatch(concept_uid=uid, rel_type=rel_type, value=value)


def _service(settings=None):
    with patch("app.services.documents.topics_computation_service.get_app_settings",
               return_value=settings or make_settings()):
        return TopicsComputationService()


def _patch_client(response):
    client = MagicMock()
    client.match = AsyncMock(return_value=response)
    return patch("app.services.documents.topics_computation_service.CrisalidTaxiClient",
                 return_value=client), client


def _document():
    return Document(titles=[TITLE], abstracts=[ABSTRACT])


async def test_disabled_returns_none_without_calling_client():
    service = _service(make_settings(enabled=False))
    patcher, client = _patch_client(make_response([topic("T1", 0.9)]))
    with patcher as client_cls:
        assert await service.compute_topics_for_document("doc-1", _document(), None) is None
        client_cls.assert_not_called()
    client.match.assert_not_called()


async def test_filters_rel_type_threshold_and_max_topics():
    service = _service(make_settings(threshold=0.6, max_topics=2))
    matches = [
        topic("T-low", 0.59),
        topic("SF", 0.99, rel_type="HAS_SUBFIELD"),
        topic("T-mid", 0.7),
        topic("T-high", 0.9),
        topic("T-third", 0.65),
    ]
    patcher, _ = _patch_client(make_response(matches))
    with patcher:
        result = await service.compute_topics_for_document("doc-1", _document(), None)
    assert result.model == "bge-m3"
    assert result.topics == [("T-high", 0.9), ("T-mid", 0.7)]
    assert len(result.input_hash) == 64


async def test_empty_matches_is_a_valid_result():
    service = _service()
    patcher, _ = _patch_client(make_response([]))
    with patcher:
        result = await service.compute_topics_for_document("doc-1", _document(), None)
    assert result is not None
    assert result.topics == []


async def test_unchanged_hash_skips_call_unless_forced():
    service = _service()
    patcher, client = _patch_client(make_response([topic("T1", 0.9)]))
    with patcher:
        first = await service.compute_topics_for_document("doc-1", _document(), None)
        assert client.match.await_count == 1
        assert await service.compute_topics_for_document(
            "doc-1", _document(), first.input_hash) is None
        assert client.match.await_count == 1
        forced = await service.compute_topics_for_document(
            "doc-1", _document(), first.input_hash, force=True)
        assert forced is not None
        assert client.match.await_count == 2


async def test_client_failure_and_short_input_return_none():
    service = _service()
    patcher, client = _patch_client(None)
    with patcher:
        assert await service.compute_topics_for_document("doc-1", _document(), None) is None
        client.match.assert_awaited_once()
        client.match.reset_mock()
        short = Document(titles=[Literal(value="Short", language="en")])
        assert await service.compute_topics_for_document("doc-1", short, None) is None
        client.match.assert_not_awaited()


async def test_client_exception_is_swallowed():
    service = _service()
    client = MagicMock()
    client.match = AsyncMock(side_effect=RuntimeError("boom"))
    with patch("app.services.documents.topics_computation_service.CrisalidTaxiClient",
               return_value=client):
        assert await service.compute_topics_for_document("doc-1", _document(), None) is None


async def test_batch_single_request_and_stats():
    service = _service()
    rows = [
        DocumentTopicsRow(uid="doc-1", titles=[TITLE], abstracts=[ABSTRACT],
                          subject_pref_labels=[]),
        DocumentTopicsRow(uid="doc-2", titles=[TITLE], abstracts=[], subject_pref_labels=[],
                          topics_input_hash="stale"),
        DocumentTopicsRow(uid="doc-short", titles=[Literal(value="Short", language="en")],
                          abstracts=[], subject_pref_labels=[]),
    ]
    patcher, client = _patch_client(make_response([topic("T1", 0.9)], ids=("doc-1", "doc-2")))
    with patcher:
        results, stats = await service.compute_topics_batch(rows)
    client.match.assert_awaited_once()
    sent_ids = [item["id"] for item in client.match.await_args[0][0]]
    assert sent_ids == ["doc-1", "doc-2"]
    assert [r.document_uid for r in results] == ["doc-1", "doc-2"]
    assert stats.computed == 2 and stats.skipped_no_input == 1 and stats.failed == 0

    # unchanged hash rows are skipped without a call
    rows[1].topics_input_hash = results[1].input_hash
    with patcher:
        results, stats = await service.compute_topics_batch(rows[1:])
    assert results == [] and stats.skipped_unchanged == 1
    assert client.match.await_count == 1


async def test_batch_failure_counts_all_inputs_as_failed():
    service = _service()
    rows = [DocumentTopicsRow(uid=f"doc-{i}", titles=[TITLE], abstracts=[ABSTRACT],
                              subject_pref_labels=[]) for i in range(3)]
    patcher, _ = _patch_client(None)
    with patcher:
        results, stats = await service.compute_topics_batch(rows)
    assert results == [] and stats.failed == 3


def test_log_missing_topics():
    service = _service()
    patcher, _ = _patch_client(None)
    result = MagicMock(topics=[("T1", 0.9), ("T2", 0.8)], document_uid="doc-1")
    with patcher:
        assert service.log_missing_topics(result, ["T1"]) == ["T2"]
