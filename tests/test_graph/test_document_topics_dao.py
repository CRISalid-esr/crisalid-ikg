from typing import cast

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord, SourceRecordDomain
from app.services.documents.document_service import DocumentService
from tests.fixtures.taxi_fixtures import TAXI_TOPIC_URI_A, TAXI_TOPIC_URI_B, \
    computed_document_for

UNKNOWN_TOPIC = "https://openalex.org/T-unknown"


def _document_dao() -> DocumentDAO:
    return cast(DocumentDAO, AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document))


def _source_record_dao() -> SourceRecordDAO:
    return cast(SourceRecordDAO,
                AbstractDAOFactory().get_dao_factory("neo4j").get_dao(SourceRecord))


async def _topic_edges(document_uid: str) -> list[dict]:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(
                "MATCH (d:Document {uid: $uid})-[r:HAS_TOPIC]->(t:Topic) "
                "RETURN t.uid AS uid, r.source AS source, r.score AS score, "
                "r.model AS model, r.computed_at IS NOT NULL AS has_computed_at "
                "ORDER BY r.source, r.score DESC",
                uid=document_uid,
            )
            return [dict(record) async for record in result]


async def _document_props(document_uid: str) -> dict:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(
                "MATCH (d:Document {uid: $uid}) RETURN d.topics_input_hash AS hash, "
                "d.topics_model AS model, d.topics_computed_at IS NOT NULL AS has_ts",
                uid=document_uid)
            return dict(await result.single())


def _row(uid: str, topics: list[tuple[str, float]], input_hash="h1", model="m1") -> dict:
    return {"document_uid": uid, "input_hash": input_hash, "model": model,
            "topics": [{"uid": t, "score": s} for t, s in topics]}


@pytest.mark.asyncio
async def test_sync_crisalid_topics_wipes_only_crisalid_edges(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        topics_document: Document,
        source_record_id_doi_1_persisted_model: SourceRecord):
    """
    Given a document with an openalex edge and a stale crisalid edge
    When crisalid topics are synced with a new list
    Then the stale crisalid edge is replaced, the openalex edge is kept and the
    hash / model / timestamp are recorded on the document
    """
    dao = _document_dao()
    uid = topics_document.uid
    # openalex edge, through source record propagation
    await _source_record_dao().sync_topics(
        source_record_id_doi_1_persisted_model.uid,
        [SourceRecordDomain(uri=TAXI_TOPIC_URI_B, score=0.5)])
    await DocumentService().update_from_source_records(None, uid)
    # stale crisalid edge
    await dao.sync_crisalid_topics(_row(uid, [(TAXI_TOPIC_URI_B, 0.4)], input_hash="old"))

    written = await dao.sync_crisalid_topics(_row(uid, [(TAXI_TOPIC_URI_A, 0.9)]))

    assert written["document_uid"] == uid
    assert written["previous_uids"] == [TAXI_TOPIC_URI_B]
    assert written["linked_uids"] == [TAXI_TOPIC_URI_A]
    edges = await _topic_edges(uid)
    assert [(e["uid"], e["source"]) for e in edges] == [
        (TAXI_TOPIC_URI_A, "crisalid"), (TAXI_TOPIC_URI_B, "openalex")]
    crisalid_edge = edges[0]
    assert crisalid_edge["score"] == pytest.approx(0.9)
    assert crisalid_edge["model"] == "m1"
    assert crisalid_edge["has_computed_at"] is True
    assert edges[1]["model"] is None
    props = await _document_props(uid)
    assert props == {"hash": "h1", "model": "m1", "has_ts": True}


@pytest.mark.asyncio
async def test_sync_crisalid_topics_unknown_uid_and_empty_list(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        topics_document: Document):
    """
    Unknown concept uids are skipped and reported; an empty list wipes the edges
    but still records the hash
    """
    dao = _document_dao()
    uid = topics_document.uid

    written = await dao.sync_crisalid_topics(
        _row(uid, [(TAXI_TOPIC_URI_A, 0.9), (UNKNOWN_TOPIC, 0.8)]))
    assert written["linked_uids"] == [TAXI_TOPIC_URI_A]
    assert len(await _topic_edges(uid)) == 1

    written = await dao.sync_crisalid_topics(_row(uid, [], input_hash="h2", model="m2"))
    assert written["previous_uids"] == [TAXI_TOPIC_URI_A]
    assert written["linked_uids"] == []
    assert await _topic_edges(uid) == []
    assert (await _document_props(uid))["hash"] == "h2"


@pytest.mark.asyncio
async def test_sync_crisalid_topics_batch_and_count(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        topics_document: Document):
    """
    The batch write returns one row per existing document and the counters reflect it
    """
    dao = _document_dao()
    uid = topics_document.uid
    written = await dao.sync_crisalid_topics_batch([
        _row(uid, [(TAXI_TOPIC_URI_A, 0.9), (TAXI_TOPIC_URI_B, 0.7)]),
        _row("does-not-exist", [(TAXI_TOPIC_URI_A, 0.9)]),
    ])
    assert len(written) == 1
    assert sorted(written[0]["linked_uids"]) == sorted([TAXI_TOPIC_URI_A, TAXI_TOPIC_URI_B])
    assert await dao.sync_crisalid_topics_batch([]) == []
    counts = await dao.count_topics_state()
    assert counts["total"] >= 1
    assert counts["computed"] == 1
    assert counts["crisalid_edges"] == 2
    assert counts["openalex_edges"] == 0
    assert await dao.get_topics_state(uid) == "h1"
    assert await dao.get_topics_state("does-not-exist") is None


@pytest.mark.asyncio
async def test_openalex_propagation_takes_max_score_and_follows_source_records(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,
        source_record_id_doi_1_hal_1_persisted_model: SourceRecord):
    """
    Given a document recorded by several source records sharing a topic with different scores
    When the document is recomputed
    Then one openalex edge exists per topic with the highest score; when the topics are
    removed from the source records and the document recomputed, the edges disappear
    """
    source_record_dao = _source_record_dao()
    await source_record_dao.sync_topics(
        source_record_id_doi_1_persisted_model.uid,
        [SourceRecordDomain(uri=TAXI_TOPIC_URI_A, score=0.7)])
    await source_record_dao.sync_topics(
        source_record_id_hal_1_persisted_model.uid,
        [SourceRecordDomain(uri=TAXI_TOPIC_URI_A, score=0.9),
         SourceRecordDomain(uri=TAXI_TOPIC_URI_B, score=0.6)])

    document = await computed_document_for(source_record_id_doi_1_hal_1_persisted_model)

    assert set(document.source_record_uids) >= {source_record_id_doi_1_persisted_model.uid,
                                                source_record_id_hal_1_persisted_model.uid}
    edges = await _topic_edges(document.uid)
    assert {(e["uid"], e["score"]) for e in edges if e["source"] == "openalex"} == {
        (TAXI_TOPIC_URI_A, 0.9), (TAXI_TOPIC_URI_B, 0.6)}
    assert {(t.source, t.uid, t.score) for t in document.topics} == {
        ("openalex", TAXI_TOPIC_URI_A, 0.9), ("openalex", TAXI_TOPIC_URI_B, 0.6)}

    await source_record_dao.sync_topics(source_record_id_hal_1_persisted_model.uid, [])
    await source_record_dao.sync_topics(source_record_id_doi_1_persisted_model.uid, [])
    await DocumentService().update_from_source_records(None, document.uid)
    assert [e for e in await _topic_edges(document.uid) if e["source"] == "openalex"] == []


@pytest.mark.asyncio
async def test_get_document_by_uid_hydrates_topics(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        topics_document: Document,
        source_record_id_doi_1_persisted_model: SourceRecord):
    """
    Document.topics carries both sources with their properties
    """
    dao = _document_dao()
    uid = topics_document.uid
    await _source_record_dao().sync_topics(
        source_record_id_doi_1_persisted_model.uid,
        [SourceRecordDomain(uri=TAXI_TOPIC_URI_B, score=0.5)])
    await DocumentService().update_from_source_records(None, uid)
    await dao.sync_crisalid_topics(_row(uid, [(TAXI_TOPIC_URI_A, 0.9)], model="bge"))

    document = await dao.get_document_by_uid(uid)

    topics = {(t.source, t.uid): t for t in document.topics}
    assert set(topics) == {("crisalid", TAXI_TOPIC_URI_A), ("openalex", TAXI_TOPIC_URI_B)}
    crisalid = topics[("crisalid", TAXI_TOPIC_URI_A)]
    assert crisalid.score == pytest.approx(0.9)
    assert crisalid.model == "bge"
    assert crisalid.display_name == "Neural Networks Stability and Synchronization"
    assert crisalid.uri == TAXI_TOPIC_URI_A
    assert topics[("openalex", TAXI_TOPIC_URI_B)].model is None
    # the rest of the hydration is unaffected
    assert len(document.titles) == 1
    assert len(document.contributions) == len(topics_document.contributions)


@pytest.mark.asyncio
async def test_get_documents_for_topics_computation(
        persisted_openalex_valid_hierarchy,  # pylint: disable=unused-argument
        topics_document: Document):
    """
    The paging query returns the literals needed to build the input and honours missing_only
    """
    dao = _document_dao()
    uid = topics_document.uid
    rows = await dao.get_documents_for_topics_computation(skip=0, limit=10, missing_only=True)
    row = next(r for r in rows if r["uid"] == uid)
    assert row["topics_input_hash"] is None
    assert row["titles"] == [{"value": "Example Article with DOI", "language": "en"}]
    assert {label["value"] for label in row["subject_pref_labels"]} >= {"Concept A"}

    await dao.sync_crisalid_topics(_row(uid, [(TAXI_TOPIC_URI_A, 0.9)]))
    rows = await dao.get_documents_for_topics_computation(skip=0, limit=10, missing_only=True)
    assert uid not in [r["uid"] for r in rows]
    rows = await dao.get_documents_for_topics_computation(skip=0, limit=10, missing_only=False)
    assert uid in [r["uid"] for r in rows]
    assert await dao.get_documents_for_topics_computation(skip=10_000, limit=10) == []
