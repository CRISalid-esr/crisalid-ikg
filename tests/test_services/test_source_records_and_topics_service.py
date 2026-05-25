import pytest

from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.agent_identifiers import PersonIdentifier
from app.models.harvesters import Harvester
from app.models.literal import Literal
from app.models.people import Person
from app.models.source_records import SourceRecord, SourceRecordDomain
from app.services.source_records.source_record_service import SourceRecordService

_TOPIC_URI_A = "https://openalex.org/T11347"
_TOPIC_URI_B = "https://openalex.org/T10080"


def _openalex_source_record(source_identifier: str, domains: list) -> SourceRecord:
    return SourceRecord(
        source_identifier=source_identifier,
        harvester=Harvester.OPENALEX.value,
        titles=[Literal(value="Test title")],
        domains=domains,
    )


async def _get_topic_links(source_record_uid: str) -> list[dict]:
    """Return [{uri, score}] for all HAS_TOPIC edges on the given source record."""
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(
                "MATCH (s:SourceRecord {uid: $uid})-[r:HAS_TOPIC]->(t:Topic) "
                "RETURN t.uri AS uri, r.score AS score",
                uid=source_record_uid,
            )
            return [{"uri": record["uri"], "score": record["score"]}
                    async for record in result]


@pytest.mark.asyncio
async def test_create_source_record_links_topics(
    persisted_openalex_valid_hierarchy,
    persisted_person_a_pydantic_model: Person,
    default_identifier_used: PersonIdentifier,
):
    """
    Given a SourceRecord with two domain entries pointing to existing Topics
    When it is created
    Then HAS_TOPIC edges exist with the correct score values
    """
    source_record = _openalex_source_record(
        "W-topic-create-test",
        domains=[
            SourceRecordDomain(uri=_TOPIC_URI_A, score=0.95),
            SourceRecordDomain(uri=_TOPIC_URI_B, score=0.80),
        ],
    )
    service = SourceRecordService()
    await service.create_source_record(
        source_record=source_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    links = await _get_topic_links(source_record.uid)
    assert len(links) == 2
    uri_to_score = {link["uri"]: link["score"] for link in links}
    assert uri_to_score[_TOPIC_URI_A] == pytest.approx(0.95)
    assert uri_to_score[_TOPIC_URI_B] == pytest.approx(0.80)


@pytest.mark.asyncio
async def test_update_source_record_replaces_topic_links(
    persisted_openalex_valid_hierarchy,
    persisted_person_a_pydantic_model: Person,
    default_identifier_used: PersonIdentifier,
):
    """
    Given a SourceRecord already created with one topic
    When it is updated with a different topic
    Then the old HAS_TOPIC edge is removed and the new one is created
    """
    service = SourceRecordService()
    source_record = _openalex_source_record(
        "W-topic-update-test",
        domains=[SourceRecordDomain(uri=_TOPIC_URI_A, score=0.90)],
    )
    await service.create_source_record(
        source_record=source_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    updated_record = _openalex_source_record(
        "W-topic-update-test",
        domains=[SourceRecordDomain(uri=_TOPIC_URI_B, score=0.70)],
    )
    await service.update_source_record(
        source_record=updated_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    links = await _get_topic_links(source_record.uid)
    assert len(links) == 1
    assert links[0]["uri"] == _TOPIC_URI_B
    assert links[0]["score"] == pytest.approx(0.70)


@pytest.mark.asyncio
async def test_create_source_record_skips_unknown_topic_uri(
    persisted_openalex_valid_hierarchy,
    persisted_person_a_pydantic_model: Person,
    default_identifier_used: PersonIdentifier,
    caplog,
):
    """
    Given a SourceRecord with a domain entry whose URI does not exist in the graph
    When it is created
    Then the source record is persisted, an error is logged, and no HAS_TOPIC edge is created
    """
    unknown_uri = "https://openalex.org/T99999"
    source_record = _openalex_source_record(
        "W-topic-unknown-test",
        domains=[SourceRecordDomain(uri=unknown_uri, score=0.50)],
    )
    service = SourceRecordService()
    await service.create_source_record(
        source_record=source_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    links = await _get_topic_links(source_record.uid)
    assert links == []
    assert unknown_uri in caplog.text


@pytest.mark.asyncio
async def test_update_source_record_with_empty_domains_clears_links(
    persisted_openalex_valid_hierarchy,
    persisted_person_a_pydantic_model: Person,
    default_identifier_used: PersonIdentifier,
):
    """
    Given a SourceRecord already linked to a Topic
    When it is updated with an empty domains list
    Then the existing HAS_TOPIC edge is removed
    """
    service = SourceRecordService()
    source_record = _openalex_source_record(
        "W-topic-clear-test",
        domains=[SourceRecordDomain(uri=_TOPIC_URI_A, score=0.88)],
    )
    await service.create_source_record(
        source_record=source_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    cleared_record = _openalex_source_record("W-topic-clear-test", domains=[])
    await service.update_source_record(
        source_record=cleared_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used,
    )

    links = await _get_topic_links(source_record.uid)
    assert links == []
