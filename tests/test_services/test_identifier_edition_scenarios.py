"""
Dedicated scenario suites for manual identifier edition (issue #385):

- removal of an identifier whose harvests mixed exclusive and shared source records;
- addition of an identifier colliding with an external person contributing to documents.

The scenario graphs are built by the fixtures in
``tests/fixtures/identifier_edition_scenarios_fixtures.py``.
"""
from types import SimpleNamespace
from typing import cast

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.identifier_types import PersonIdentifierType
from app.models.source_records import SourceRecord
from app.services.people.people_service import PeopleService
from app.services.source_records.source_record_service import SourceRecordService
from app.signals import document_sources_changed
from tests.fixtures.identifier_edition_scenarios_fixtures import (
    CLAIRE_UID, CLAIRE_IDREF, CLAIRE_ORCID, CLAIRE_IDHALS, RACHID_UID,
    PIERRE_UID, PIERRE_IDREF, PIERRE_ORCID,
    SP_CLAIRE_SCANR_UID, SP_CLAIRE_HAL_UID, SP_RACHID_HAL_UID,
    SP_EVA_UID, SP_MARTA_UID
)

TIMESTAMP = "2026-07-12T10:00:00.000Z"


async def _run_read_query(query: str, **params) -> int:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["count"]


async def _count_source_people(source_person_uid: str) -> int:
    return await _run_read_query(
        "MATCH (sp:SourcePerson {uid: $uid}) RETURN count(sp) AS count",
        uid=source_person_uid)


async def _count_recorded_by(person_uid: str, source_person_uid: str) -> int:
    return await _run_read_query(
        "MATCH (:Person {uid: $person_uid})-[r:RECORDED_BY]->"
        "(:SourcePerson {uid: $source_person_uid}) RETURN count(r) AS count",
        person_uid=person_uid, source_person_uid=source_person_uid)


async def _count_orphan_source_people() -> int:
    return await _run_read_query(
        "MATCH (sp:SourcePerson) WHERE NOT (sp)<-[:CONTRIBUTOR]-(:SourceContribution) "
        "RETURN count(sp) AS count")


async def _count_orphan_source_contributions() -> int:
    return await _run_read_query(
        "MATCH (c:SourceContribution) WHERE NOT (c)<-[:HAS_CONTRIBUTION]-(:SourceRecord) "
        "RETURN count(c) AS count")


async def _count_nodes(label: str, **props) -> int:
    conditions = " AND ".join(f"n.{key} = ${key}" for key in props)
    where = f" WHERE {conditions}" if conditions else ""
    return await _run_read_query(
        f"MATCH (n:{label}){where} RETURN count(n) AS count", **props)


async def _count_identifier_owners(identifier_type: str, value: str,
                                   external: bool | None = None) -> int:
    external_filter = "" if external is None else " {external: $external}"
    return await _run_read_query(
        f"MATCH (p:Person{external_filter})-[:HAS_IDENTIFIER]->"
        "(:AgentIdentifier {type: $identifier_type, value: $value}) "
        "RETURN count(p) AS count",
        identifier_type=identifier_type, value=value,
        **({"external": external} if external is not None else {}))


async def _count_document_contributions(person_uid: str) -> int:
    return await _run_read_query(
        "MATCH (:Person {uid: $person_uid})-[:HAS_CONTRIBUTION]->(c:Contribution)"
        "<-[:HAS_CONTRIBUTION]-(:Document) RETURN count(c) AS count",
        person_uid=person_uid)


def _source_record_dao() -> SourceRecordDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(SourceRecordDAO, factory.get_dao(SourceRecord))


def _document_dao() -> DocumentDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(DocumentDAO, factory.get_dao(Document))


async def _remove_claire_idref():
    await PeopleService().remove_identifier(
        CLAIRE_UID, PersonIdentifierType.IDREF.value, CLAIRE_IDREF)


# ---------------------------------------------------------------------------
# Removal scenario
# ---------------------------------------------------------------------------


async def test_removal_deletes_exclusive_records_and_keeps_shared_ones(
        identifier_removal_scenario: SimpleNamespace,
) -> None:
    """
    Given records harvested through Claire's idref, some exclusive and some shared
    When the idref is removed
    Then exclusive records are deleted, shared records only lose Claire's edge,
        and records harvested through her other identifiers are untouched
    """
    scenario = identifier_removal_scenario
    await _remove_claire_idref()

    service = SourceRecordService()
    assert await service.source_record_exists(scenario.rec_exclusive_uid) is False
    assert await service.source_record_exists(scenario.rec_no_recorded_by_uid) is False
    assert await service.source_record_exists(scenario.rec_shared_uid) is True
    assert await service.source_record_exists(scenario.rec_sp_shared_uid) is True

    source_record_dao = _source_record_dao()
    assert await source_record_dao.count_harvested_for(scenario.rec_shared_uid) == 1
    assert await source_record_dao.count_harvested_for(scenario.rec_sp_shared_uid) == 1
    # the shared record now belongs to Rachid only (his legacy edge carries
    # no identifier_used properties, as on the production graph)
    assert await source_record_dao.get_source_record_uids_by_identifier_used(
        CLAIRE_UID, PersonIdentifierType.IDREF, CLAIRE_IDREF) == []
    # the orcid-harvested record is still Claire's
    assert scenario.rec_sp_shared_uid in (
        await source_record_dao.get_source_record_uids_by_identifier_used(
            CLAIRE_UID, PersonIdentifierType.ORCID, CLAIRE_ORCID))


async def test_removal_cleans_source_layer_without_orphans(
        identifier_removal_scenario: SimpleNamespace,
) -> None:
    """
    Given the mixed harvest scenario
    When the idref is removed
    Then orphaned SourcePersons are deleted, shared SourcePersons survive with the
        guarded RECORDED_BY edges, and no orphan source-layer node remains
    """
    scenario = identifier_removal_scenario  # pylint: disable=unused-variable
    await _remove_claire_idref()

    # Éva (only contributor of the deleted exclusive record) and Marta (only
    # contributor of the deleted no-recorded-by record) are gone
    assert await _count_source_people(SP_EVA_UID) == 0
    assert await _count_source_people(SP_MARTA_UID) == 0
    # Claire's scanr SourcePerson survives: it still contributes to the
    # orcid-harvested thesis, and her RECORDED_BY edge is preserved
    assert await _count_source_people(SP_CLAIRE_SCANR_UID) == 1
    assert await _count_recorded_by(CLAIRE_UID, SP_CLAIRE_SCANR_UID) == 1
    # Claire's hal SourcePerson survives inside the shared record, but her
    # RECORDED_BY edge to it is gone (the record is not hers anymore)
    assert await _count_source_people(SP_CLAIRE_HAL_UID) == 1
    assert await _count_recorded_by(CLAIRE_UID, SP_CLAIRE_HAL_UID) == 0
    # Rachid's path is untouched
    assert await _count_source_people(SP_RACHID_HAL_UID) == 1
    assert await _count_recorded_by(RACHID_UID, SP_RACHID_HAL_UID) == 1

    assert await _count_orphan_source_people() == 0
    assert await _count_orphan_source_contributions() == 0


async def test_removal_preserves_shared_entities(
        identifier_removal_scenario: SimpleNamespace,
) -> None:
    """
    Given the deleted exclusive record carried a journal, an issue and an
        affiliation to a source organization
    When the idref is removed
    Then the SourceJournal, SourceIssue and SourceOrganization nodes survive
    """
    scenario = identifier_removal_scenario  # pylint: disable=unused-variable
    await _remove_claire_idref()

    assert await _count_nodes(
        "SourceOrganization", source_identifier="scanr_idref_900000001") == 1
    assert await _count_nodes(
        "SourceIssue", source_identifier="cahiers_histoire_sociale-ScanR") == 1
    assert await _count_nodes(
        "SourceJournal") >= 1


async def test_removal_recomputes_documents(
        identifier_removal_scenario: SimpleNamespace,
        mocked_exchange,
) -> None:
    """
    Given documents computed from the harvested records
    When the idref is removed
    Then the shared record's document loses Claire's contribution but keeps
        Rachid's, the orcid-harvested document keeps Claire's contribution,
        and the document events are emitted on the interactive routing keys
    """
    scenario = identifier_removal_scenario
    mocked_exchange.publish.reset_mock()
    await _remove_claire_idref()

    document_dao = _document_dao()
    shared_document = await document_dao.get_document_by_source_record_uid(
        scenario.rec_shared_uid)
    assert shared_document is not None
    contributor_uids = [contribution.contributor.uid
                        for contribution in shared_document.contributions]
    assert CLAIRE_UID not in contributor_uids
    assert RACHID_UID in contributor_uids

    sp_shared_document = await document_dao.get_document_by_source_record_uid(
        scenario.rec_sp_shared_uid)
    assert sp_shared_document is not None
    assert CLAIRE_UID in [contribution.contributor.uid
                          for contribution in sp_shared_document.contributions]

    document_routing_keys = [
        call.kwargs["routing_key"] for call in mocked_exchange.publish.call_args_list
        if call.kwargs["routing_key"].startswith("event.documents.document.")
    ]
    assert document_routing_keys
    assert all(routing_key.endswith(".interactive") for routing_key in document_routing_keys)


async def test_removal_of_unused_identifier_leaves_harvests_untouched(
        identifier_removal_scenario: SimpleNamespace,
) -> None:
    """
    Given Claire also holds an idhals identifier never used as a harvesting key
    When that idhals is removed
    Then every harvested record and edge survives
    """
    scenario = identifier_removal_scenario
    await PeopleService().remove_identifier(
        CLAIRE_UID, PersonIdentifierType.IDHALS.value, CLAIRE_IDHALS)

    service = SourceRecordService()
    for record_uid in [scenario.rec_exclusive_uid, scenario.rec_shared_uid,
                       scenario.rec_sp_shared_uid, scenario.rec_no_recorded_by_uid]:
        assert await service.source_record_exists(record_uid) is True
    source_record_dao = _source_record_dao()
    assert len(await source_record_dao.get_source_record_uids_by_identifier_used(
        CLAIRE_UID, PersonIdentifierType.IDREF, CLAIRE_IDREF)) == 3
    person = await PeopleService().get_person(CLAIRE_UID)
    assert person.get_identifier(PersonIdentifierType.IDHALS) is None
    assert person.get_identifier(PersonIdentifierType.IDREF) is not None


# ---------------------------------------------------------------------------
# Addition / collision scenario
# ---------------------------------------------------------------------------


async def test_addition_detaches_colliding_external_identifier(
        identifier_collision_scenario: SimpleNamespace,
) -> None:
    """
    Given an external co-author aligned with idref and orcid identifiers
    When the same idref is added to the internal person
    Then the external person loses only the colliding identifier edge and keeps
        its other identifier, its display name and its document contributions
    """
    scenario = identifier_collision_scenario
    people_service = PeopleService()
    assert await _count_document_contributions(scenario.external_pierre_uid) == 1

    await people_service.add_identifier(
        PIERRE_UID, PersonIdentifierType.IDREF.value, PIERRE_IDREF, False, TIMESTAMP)

    # one owner per identifier: the internal person only
    assert await _count_identifier_owners("idref", PIERRE_IDREF) == 1
    assert await _count_identifier_owners("idref", PIERRE_IDREF, external=False) == 1
    internal_pierre = await people_service.get_person(PIERRE_UID)
    idref_identifier = internal_pierre.get_identifier(PersonIdentifierType.IDREF)
    assert idref_identifier.value == PIERRE_IDREF
    assert idref_identifier.validated is True
    assert idref_identifier.authenticated is False

    # the external person survives with its orcid, its name and its contribution
    external_pierre = await people_service.get_person(scenario.external_pierre_uid)
    assert external_pierre is not None
    assert external_pierre.get_identifier(PersonIdentifierType.IDREF) is None
    assert external_pierre.get_identifier(PersonIdentifierType.ORCID) is not None
    assert external_pierre.display_name == "Vasseur, Pierre"
    assert await _count_document_contributions(scenario.external_pierre_uid) == 1


async def test_addition_of_authenticated_identifier_detaches_external_owner(
        identifier_collision_scenario: SimpleNamespace,
) -> None:
    """
    Given the external co-author also owns the orcid identifier
    When the same orcid is added to the internal person through authentication
    Then the identifier is authenticated on the internal person and detached from
        the external one, which keeps its idref
    """
    scenario = identifier_collision_scenario
    people_service = PeopleService()

    await people_service.add_identifier(
        PIERRE_UID, PersonIdentifierType.ORCID.value, PIERRE_ORCID, True, TIMESTAMP)

    assert await _count_identifier_owners("orcid", PIERRE_ORCID) == 1
    internal_pierre = await people_service.get_person(PIERRE_UID)
    orcid_identifier = internal_pierre.get_identifier(PersonIdentifierType.ORCID)
    assert orcid_identifier.authenticated is True
    assert orcid_identifier.validated is True
    assert orcid_identifier.authentication_date is not None

    external_pierre = await people_service.get_person(scenario.external_pierre_uid)
    assert external_pierre.get_identifier(PersonIdentifierType.ORCID) is None
    assert external_pierre.get_identifier(PersonIdentifierType.IDREF) is not None


async def test_addition_then_recompute_repoints_contribution_to_internal_person(
        identifier_collision_scenario: SimpleNamespace,
) -> None:
    """
    Given the internal person now owns every identifier carried by the co-author
        SourcePerson (idref and orcid)
    When the document is recomputed from its source records
    Then the contribution is re-pointed from the external person to the internal one

    Note: both identifiers must be claimed — the SourcePerson carries idref AND
    orcid, and the contributor matching resolves through any of them, so as long
    as the external person still owns one of the two the re-pointing is ambiguous.
    """
    scenario = identifier_collision_scenario
    people_service = PeopleService()
    await people_service.add_identifier(
        PIERRE_UID, PersonIdentifierType.IDREF.value, PIERRE_IDREF, False, TIMESTAMP)
    await people_service.add_identifier(
        PIERRE_UID, PersonIdentifierType.ORCID.value, PIERRE_ORCID, True, TIMESTAMP)

    await document_sources_changed.send_async(None, document_uid=scenario.document_uid)

    document = await _document_dao().get_document_by_source_record_uid(
        scenario.rec_coauthored_uid)
    assert document is not None
    contributor_uids = [contribution.contributor.uid
                        for contribution in document.contributions]
    assert PIERRE_UID in contributor_uids
    assert scenario.external_pierre_uid not in contributor_uids


async def test_addition_without_collision_leaves_external_persons_untouched(
        identifier_collision_scenario: SimpleNamespace,
) -> None:
    """
    Given the external co-author and its identifiers
    When the internal person adds an identifier nobody else owns
    Then the external person's identifiers are untouched
    """
    scenario = identifier_collision_scenario
    people_service = PeopleService()

    await people_service.add_identifier(
        PIERRE_UID, PersonIdentifierType.IDHALS.value, "pierre-vasseur", False, TIMESTAMP)

    external_pierre = await people_service.get_person(scenario.external_pierre_uid)
    assert external_pierre.get_identifier(PersonIdentifierType.IDREF) is not None
    assert external_pierre.get_identifier(PersonIdentifierType.ORCID) is not None
    assert await _count_identifier_owners("idref", PIERRE_IDREF, external=True) == 1
