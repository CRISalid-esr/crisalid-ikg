from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from app.amqp.amqp_document_event_message_factory import AMQPDocumentEventMessageFactory
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.services.documents.crisalid_taxi_client import CrisalidTaxiClient
from app.services.documents.document_service import DocumentService
from tests.fixtures.taxi_fixtures import TAXI_MODEL, TAXI_TOPIC_URI_A, TAXI_TOPIC_URI_B


def _document_dao() -> DocumentDAO:
    return cast(DocumentDAO, AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document))


def _crisalid_topics(document: Document) -> dict[str, float]:
    return {t.uid: t.score for t in document.topics if t.source == "crisalid"}


@pytest.mark.asyncio
async def test_recompute_writes_crisalid_topics_and_oa_status(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        taxi_enabled_settings,  # pylint: disable=unused-argument
        mock_taxi_client: AsyncMock,
        topics_document: Document):
    """
    Given Crisalid-taxi enabled and answering
    When a document is recomputed
    Then crisalid topics are written (subfield match ignored) together with the OA status,
    and the AMQP payload carries them
    """
    uid = topics_document.uid
    await DocumentService().update_from_source_records(None, uid)

    mock_taxi_client.assert_awaited_once()
    sent = mock_taxi_client.await_args[0][0]
    assert sent[0]["id"] == uid
    assert sent[0]["text"].startswith("Example Article with DOI")
    document = await _document_dao().get_document_by_uid(uid)
    assert _crisalid_topics(document) == {TAXI_TOPIC_URI_A: pytest.approx(0.91),
                                          TAXI_TOPIC_URI_B: pytest.approx(0.72)}
    assert all(t.model == TAXI_MODEL for t in document.topics)
    assert document.open_access_status.oa_computation_timestamp is not None
    assert await _document_dao().get_topics_state(uid) is not None

    payload = await AMQPDocumentEventMessageFactory._build_document_message_payload(uid)  # pylint: disable=protected-access
    assert {(t["source"], t["uid"]) for t in payload["topics"]} == {
        ("crisalid", TAXI_TOPIC_URI_A), ("crisalid", TAXI_TOPIC_URI_B)}
    assert payload["topics"][0]["model"] == TAXI_MODEL


@pytest.mark.asyncio
async def test_unchanged_input_skips_taxi_call(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        taxi_enabled_settings,  # pylint: disable=unused-argument
        mock_taxi_client: AsyncMock,
        topics_document: Document):
    """
    A second recomputation with the same title / abstract / subjects does not call Taxi
    but keeps the links
    """
    uid = topics_document.uid
    await DocumentService().update_from_source_records(None, uid)
    await DocumentService().update_from_source_records(None, uid)
    mock_taxi_client.assert_awaited_once()
    document = await _document_dao().get_document_by_uid(uid)
    assert set(_crisalid_topics(document)) == {TAXI_TOPIC_URI_A, TAXI_TOPIC_URI_B}


@pytest.mark.asyncio
async def test_taxi_failure_keeps_previous_links_and_hash(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        taxi_enabled_settings,  # pylint: disable=unused-argument
        mock_taxi_client: AsyncMock,
        topics_document: Document):
    """
    When Taxi fails, the document is still computed and the previous crisalid links
    and hash are left untouched
    """
    uid = topics_document.uid
    dao = _document_dao()
    await DocumentService().update_from_source_records(None, uid)
    previous_hash = await dao.get_topics_state(uid)
    # force a new input hash so that Taxi would be called, and make it fail
    await dao.sync_crisalid_topics({"document_uid": uid, "input_hash": "stale",
                                    "model": "old", "topics": [{"uid": TAXI_TOPIC_URI_B,
                                                                "score": 0.1}]})
    mock_taxi_client.side_effect = None
    mock_taxi_client.return_value = None

    await DocumentService().update_from_source_records(None, uid)

    assert mock_taxi_client.await_count == 2
    document = await dao.get_document_by_uid(uid)
    assert document.to_be_recomputed is False
    assert _crisalid_topics(document) == {TAXI_TOPIC_URI_B: pytest.approx(0.1)}
    assert await dao.get_topics_state(uid) == "stale"
    assert previous_hash != "stale"


@pytest.mark.asyncio
async def test_taxi_disabled_never_calls_client(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        mock_taxi_client: AsyncMock,
        topics_document: Document):
    """
    With TAXI_ENABLED=false (test default) nothing is called and no topic state is written
    """
    uid = topics_document.uid
    with patch.object(CrisalidTaxiClient, "__init__", side_effect=AssertionError("no client")):
        await DocumentService().update_from_source_records(None, uid)
    mock_taxi_client.assert_not_awaited()
    assert await _document_dao().get_topics_state(uid) is None
    assert (await _document_dao().get_document_by_uid(uid)).topics == []
