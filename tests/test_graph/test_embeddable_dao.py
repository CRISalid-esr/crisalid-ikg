import pytest

from app.graph.neo4j.embeddable_dao import EmbeddableDAO
from app.graph.neo4j.neo4j_setup import Neo4jSetup
from app.models.concepts import Concept
from app.models.people import Person


async def test_get_pending_nodes_returns_embeddable_literals_after_concept_creation(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    nodes = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)

    assert len(nodes) >= 2
    for node in nodes:
        assert "element_id" in node
        assert "value" in node
        assert "type" in node
        assert node["type"] in Neo4jSetup._EMBEDDABLE_TYPES


async def test_get_pending_nodes_filters_by_type(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    nodes = await dao.get_pending_nodes(
        statuses=["pending"], types=["concept_pref_label"], batch_size=100
    )

    assert len(nodes) >= 1
    assert all(n["type"] == "concept_pref_label" for n in nodes)


async def test_get_pending_nodes_excludes_by_model(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    pending = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert pending

    target = pending[0]
    await dao.update_embeddings_batch([{
        "element_id": target["element_id"],
        "embedding": [0.1, 0.2],
        "embedding_hash": "abc",
        "embedding_model": "model-v1",
    }])

    remaining = await dao.get_pending_nodes(
        statuses=["pending"], model_exclude="model-v1", batch_size=100
    )
    remaining_ids = {n["element_id"] for n in remaining}
    assert target["element_id"] not in remaining_ids


async def test_update_embeddings_batch_sets_success_status(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    pending = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert pending

    target = pending[0]
    await dao.update_embeddings_batch([{
        "element_id": target["element_id"],
        "embedding": [0.1, 0.2],
        "embedding_hash": "testhash",
        "embedding_model": "m1",
    }])

    success_nodes = await dao.get_pending_nodes(statuses=["success"], batch_size=100)
    success_ids = {n["element_id"] for n in success_nodes}
    assert target["element_id"] in success_ids


async def test_mark_failed_sets_failed_status(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    pending = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert pending

    target = pending[0]
    await dao.mark_failed(target["element_id"], "connection timeout")

    counts = await dao.count_by_status()
    assert counts.get("failed", 0) >= 1

    failed_nodes = await dao.get_pending_nodes(statuses=["failed"], batch_size=100)
    failed_ids = {n["element_id"] for n in failed_nodes}
    assert target["element_id"] in failed_ids


async def test_count_by_status_reflects_mixed_statuses(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    pending = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert len(pending) >= 2

    await dao.mark_failed(pending[0]["element_id"], "err")
    await dao.update_embeddings_batch([{
        "element_id": pending[1]["element_id"],
        "embedding": [0.5],
        "embedding_hash": "h",
        "embedding_model": "m",
    }])

    counts = await dao.count_by_status()
    assert counts.get("failed", 0) >= 1
    assert counts.get("success", 0) >= 1


async def test_reset_all_for_migration_clears_embeddings(
        persisted_concept_a_pydantic_model: Concept,
):
    dao = EmbeddableDAO()
    pending = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert pending

    await dao.update_embeddings_batch([{
        "element_id": pending[0]["element_id"],
        "embedding": [0.1],
        "embedding_hash": "h",
        "embedding_model": "m",
    }])

    success_before = await dao.get_pending_nodes(statuses=["success"], batch_size=100)
    assert success_before

    await dao.reset_all_for_migration()

    success_after = await dao.get_pending_nodes(statuses=["success"], batch_size=100)
    assert not success_after

    pending_after = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)
    assert len(pending_after) >= len(pending)


async def test_get_pending_nodes_excludes_non_embeddable_person_literals(
        persisted_person_a_pydantic_model: Person,
):
    dao = EmbeddableDAO()
    nodes = await dao.get_pending_nodes(statuses=["pending"], batch_size=100)

    non_embeddable = {"person_first_name", "person_last_name"}
    for node in nodes:
        assert node["type"] not in non_embeddable
