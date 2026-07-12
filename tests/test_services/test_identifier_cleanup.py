"""
Tests for the harvested-data cleanup triggered by a person identifier removal (issue #385).
"""
from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.people.people_service import PeopleService
from app.services.source_records.source_record_service import SourceRecordService
from tests.fixtures.common import _source_record_from_json_data

PERSON_A_UID = "local-jdoe@univ-domain.edu"
PERSON_B_UID = "local-jdurand@univ-domain.edu"
IDREF_VALUE = "122758765"
TIMESTAMP = "2025-08-26T06:17:28.243Z"


def _inject_mocked_exchange(test_app, mocked_exchange):
    test_app.amqp_interface.pika_exchanges[
        get_app_settings().amqp_graph_exchange_name] = mocked_exchange


def _source_record_dao() -> SourceRecordDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(SourceRecordDAO, factory.get_dao(SourceRecord))


def _document_dao() -> DocumentDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(DocumentDAO, factory.get_dao(Document))


async def _run_read_query(query: str, **params) -> int:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["count"]


async def _count_source_people_by_uid(source_person_uid: str) -> int:
    return await _run_read_query(
        "MATCH (sp:SourcePerson {uid: $uid}) RETURN count(sp) AS count",
        uid=source_person_uid)


async def _count_orphan_source_people() -> int:
    return await _run_read_query(
        "MATCH (sp:SourcePerson) WHERE NOT (sp)<-[:CONTRIBUTOR]-(:SourceContribution) "
        "RETURN count(sp) AS count")


async def _count_orphan_source_contributions() -> int:
    return await _run_read_query(
        "MATCH (c:SourceContribution) WHERE NOT (c)<-[:HAS_CONTRIBUTION]-(:SourceRecord) "
        "RETURN count(c) AS count")


async def _count_recorded_by(person_uid: str, source_person_uid: str) -> int:
    return await _run_read_query(
        "MATCH (:Person {uid: $person_uid})-[r:RECORDED_BY]->"
        "(:SourcePerson {uid: $source_person_uid}) RETURN count(r) AS count",
        person_uid=person_uid, source_person_uid=source_person_uid)


async def _prepare_person_a_with_idref_record(
        person_a: Person, source_record: SourceRecord,
        identifier_used: PersonIdentifier) -> SourceRecord:
    """
    Give person A the idref identifier and persist the source record harvested
    for them through that identifier; return the persisted record.
    """
    people_service = PeopleService()
    await people_service.add_identifier(
        person_a.uid, PersonIdentifierType.IDREF.value, IDREF_VALUE, False, TIMESTAMP)
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=source_record,
        harvested_for=person_a,
        identifier_used=identifier_used)
    return await source_record_service.get_source_record(source_record.uid)


async def test_cleanup_exclusive_source_record(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        mocked_exchange,
        persisted_person_a_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Case 1: given a source record harvested exclusively for a person through an identifier,
    when the identifier is removed,
    then the record and its source layer are deleted, no orphans remain,
    and the affected document events are emitted on the interactive routing keys.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    record = await _prepare_person_a_with_idref_record(
        persisted_person_a_pydantic_model,
        scanr_record_with_person_a_as_contributor_pydantic_model,
        default_identifier_used)
    source_person_uid = record.contributions[0].contributor.uid

    document_before = await _document_dao().get_document_by_source_record_uid(record.uid)
    assert document_before is not None
    mocked_exchange.publish.reset_mock()

    await PeopleService().remove_identifier(
        PERSON_A_UID, PersonIdentifierType.IDREF.value, IDREF_VALUE)

    source_record_service = SourceRecordService()
    assert await source_record_service.source_record_exists(record.uid) is False
    assert await _count_source_people_by_uid(source_person_uid) == 0
    assert await _count_orphan_source_people() == 0
    assert await _count_orphan_source_contributions() == 0

    document_routing_keys = [
        call.kwargs["routing_key"] for call in mocked_exchange.publish.call_args_list
        if call.kwargs["routing_key"].startswith("event.documents.document.")
    ]
    assert document_routing_keys
    assert all(routing_key.endswith(".interactive") for routing_key in document_routing_keys)


async def test_cleanup_shared_source_record(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        mocked_exchange,
        persisted_person_a_pydantic_model: Person,
        persisted_person_b_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Case 2: given a source record shared by two persons,
    when the first person's harvesting identifier is removed,
    then only their harvesting path is detached, the record and the other person's path
    survive, and the recomputed document no longer carries the first person's contribution.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    record = await _prepare_person_a_with_idref_record(
        persisted_person_a_pydantic_model,
        scanr_record_with_person_a_as_contributor_pydantic_model,
        default_identifier_used)
    source_person_uid = record.contributions[0].contributor.uid
    # share the record with person B, harvested through B's own idref
    person_b_identifier_used = PersonIdentifier(
        type=PersonIdentifierType.IDREF, value="012345678")
    source_record_service = SourceRecordService()
    await source_record_service.update_source_record(
        source_record=scanr_record_with_person_a_as_contributor_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model,
        identifier_used=person_b_identifier_used)

    document_before = await _document_dao().get_document_by_source_record_uid(record.uid)
    assert document_before is not None
    assert any(contribution.contributor.uid == PERSON_A_UID
               for contribution in document_before.contributions)

    await PeopleService().remove_identifier(
        PERSON_A_UID, PersonIdentifierType.IDREF.value, IDREF_VALUE)

    assert await source_record_service.source_record_exists(record.uid) is True
    source_record_dao = _source_record_dao()
    assert await source_record_dao.get_source_record_uids_by_identifier_used(
        PERSON_A_UID, PersonIdentifierType.IDREF, IDREF_VALUE) == []
    assert record.uid in await source_record_dao.get_source_record_uids_by_identifier_used(
        PERSON_B_UID, PersonIdentifierType.IDREF, "012345678")
    assert await source_record_dao.count_harvested_for(record.uid) == 1
    assert await _count_recorded_by(PERSON_A_UID, source_person_uid) == 0

    document_after = await _document_dao().get_document_by_source_record_uid(record.uid)
    assert document_after is not None
    assert all(contribution.contributor.uid != PERSON_A_UID
               for contribution in document_after.contributions)


async def test_cleanup_preserves_source_person_shared_with_other_record(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        mocked_exchange,
        persisted_person_a_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        scanr_record_with_person_a_as_contributor_json_data: dict,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Guard: given two records sharing the same SourcePerson, both harvested for the person
    but through different identifiers,
    when the identifier of the first record is removed,
    then the SourcePerson and the person's RECORDED_BY edge survive for the second record.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    record = await _prepare_person_a_with_idref_record(
        persisted_person_a_pydantic_model,
        scanr_record_with_person_a_as_contributor_pydantic_model,
        default_identifier_used)
    source_person_uid = record.contributions[0].contributor.uid

    # a second record with the same contributor, harvested through person A's orcid
    other_record_json = dict(scanr_record_with_person_a_as_contributor_json_data)
    other_record_json["source_identifier"] = "doi10.9999/other-record"
    other_record_json["identifiers"] = [{"type": "doi", "value": "10.9999/other-record"}]
    other_record = _source_record_from_json_data(other_record_json)
    orcid_identifier_used = PersonIdentifier(
        type=PersonIdentifierType.ORCID, value="0000-0001-2345-6789")
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=other_record,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=orcid_identifier_used)

    await PeopleService().remove_identifier(
        PERSON_A_UID, PersonIdentifierType.IDREF.value, IDREF_VALUE)

    assert await source_record_service.source_record_exists(record.uid) is False
    assert await source_record_service.source_record_exists(other_record.uid) is True
    assert await _count_source_people_by_uid(source_person_uid) == 1
    assert await _count_recorded_by(PERSON_A_UID, source_person_uid) == 1


async def test_confirm_identifier_triggers_no_cleanup(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        mocked_exchange,
        persisted_person_a_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        default_identifier_used: PersonIdentifier,
) -> None:
    """
    Trigger discipline: confirming (authenticating/validating) an identifier without
    changing its value must not clean up any harvested data.
    """
    _inject_mocked_exchange(test_app, mocked_exchange)
    record = await _prepare_person_a_with_idref_record(
        persisted_person_a_pydantic_model,
        scanr_record_with_person_a_as_contributor_pydantic_model,
        default_identifier_used)

    await PeopleService().confirm_identifier(
        PERSON_A_UID, PersonIdentifierType.IDREF.value, IDREF_VALUE, False, TIMESTAMP)

    source_record_service = SourceRecordService()
    assert await source_record_service.source_record_exists(record.uid) is True
    source_record_dao = _source_record_dao()
    assert record.uid in await source_record_dao.get_source_record_uids_by_identifier_used(
        PERSON_A_UID, PersonIdentifierType.IDREF, IDREF_VALUE)
