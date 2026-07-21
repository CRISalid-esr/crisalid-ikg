"""
Tests for contribution/person consistency under concurrent external-people merges
(issue #412): a contribution must never resurrect a deleted Person as a bare node,
and merging external people must preserve their contributions.
"""
from itertools import permutations
from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.person_dao import PersonDAO
from app.models.document import Document
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_contributors.source_contributor_mapping_service import \
    SourceContributorMappingService
from app.services.source_records.equivalence_service import EquivalenceService
from app.signals import source_record_created, source_record_updated, \
    document_sources_changed, document_created_from_sources

AUTHOR_ROLE = "http://id.loc.gov/vocabulary/relators/aut"


def _document_dao() -> DocumentDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(DocumentDAO, factory.get_dao(Document))


def _person_dao() -> PersonDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return cast(PersonDAO, factory.get_dao(Person))


async def _run_count_query(query: str, **params) -> int:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, **params)
            record = await result.single()
            return record["count"]


async def _count_persons_by_uid(person_uid: str) -> int:
    return await _run_count_query(
        "MATCH (p:Person {uid: $uid}) RETURN count(p) AS count", uid=person_uid)


async def _count_bare_persons() -> int:
    """Persons with no display_name and no HAS_NAME relation (resurrection footprint)."""
    return await _run_count_query(
        "MATCH (p:Person) WHERE p.display_name IS NULL AND NOT (p)-[:HAS_NAME]->() "
        "RETURN count(p) AS count")


async def _count_document_contributions(document_uid: str) -> int:
    return await _run_count_query(
        "MATCH (:Document {uid: $uid})-[:HAS_CONTRIBUTION]->(c:Contribution) "
        "RETURN count(c) AS count", uid=document_uid)


async def _count_contributions_between(document_uid: str, person_uid: str) -> int:
    return await _run_count_query(
        "MATCH (:Document {uid: $document_uid})-[:HAS_CONTRIBUTION]->(c:Contribution)"
        "<-[:HAS_CONTRIBUTION]-(:Person {uid: $person_uid}) RETURN count(c) AS count",
        document_uid=document_uid, person_uid=person_uid)


async def _count_orphan_contributions() -> int:
    return await _run_count_query(
        "MATCH (c:Contribution) WHERE NOT (c)<-[:HAS_CONTRIBUTION]-(:Person) "
        "RETURN count(c) AS count")


async def _create_document_for_source_record(source_record: SourceRecord) -> Document:
    """Create the document of a source record through the equivalence service."""
    with source_record_updated.muted(), source_record_created.muted(), \
            document_sources_changed.muted(), document_created_from_sources.muted():
        await EquivalenceService().update_source_record(None, source_record.uid)
    document = await _document_dao().get_document_by_source_record_uid(source_record.uid)
    assert document is not None
    return document


async def test_create_contribution_with_missing_person_creates_nothing(
        persisted_person_a_pydantic_model: Person,
        hal_article_a_source_record_persisted_model: SourceRecord,
) -> None:
    """
    Given an existing document
    When a contribution is created for a person uid that does not exist
    Then no contribution is created and no bare Person node appears
    """
    document = await _create_document_for_source_record(
        hal_article_a_source_record_persisted_model)
    # depending on registered signal receivers, the document may already carry
    # contributions at this point: assert on the delta, not on an absolute count
    contributions_before = await _count_document_contributions(document.uid)
    contribution_id = await _document_dao().create_contribution(
        document_uid=document.uid,
        person_uid="ghost-person",
        roles=[AUTHOR_ROLE])
    assert contribution_id is None
    assert await _count_persons_by_uid("ghost-person") == 0
    assert await _count_document_contributions(document.uid) == contributions_before
    assert await _count_bare_persons() == 0


async def test_create_contribution_with_missing_document_creates_nothing(
        persisted_person_a_pydantic_model: Person,
) -> None:
    """
    Given an existing person
    When a contribution is created for a document uid that does not exist
    Then no contribution and no bare Document node are created
    """
    contribution_id = await _document_dao().create_contribution(
        document_uid="ghost-document",
        person_uid=persisted_person_a_pydantic_model.uid,
        roles=[AUTHOR_ROLE])
    assert contribution_id is None
    assert await _run_count_query(
        "MATCH (d:Document {uid: 'ghost-document'}) RETURN count(d) AS count") == 0


async def test_contribution_mapping_recovers_from_concurrent_merge(
        persisted_person_a_pydantic_model: Person,  # pylint: disable=unused-argument
        hal_article_a_source_record_persisted_model: SourceRecord,
) -> None:
    """
    Given a document whose contributor clusters have been linked to people
    When one linked external person is deleted by a concurrent merge before
    the contributions are written
    Then the contribution is re-resolved onto the surviving person and no bare
    Person node is created
    """
    source_record = hal_article_a_source_record_persisted_model
    document = await _create_document_for_source_record(source_record)
    service = SourceContributorMappingService(
        source_records=[source_record], document_uid=document.uid)
    # pylint: disable=protected-access
    linked_people = await service._link_source_people_to_people()
    stale_person_uid = "hal-863912"
    assert stale_person_uid in linked_people
    # Simulate a concurrent run merging the linked person into a survivor:
    # the person node is deleted and its RECORDED_BY relations are re-pointed
    surviving_person = Person(
        uid="scanr-idref00000001", display_name="Jérôme Février", external=True)
    await _person_dao().create(surviving_person)
    await _person_dao().merge_people(surviving_person.uid, stale_person_uid)
    assert await _count_persons_by_uid(stale_person_uid) == 0

    await service._update_contributions(linked_people)

    # the stale person was not resurrected
    assert await _count_persons_by_uid(stale_person_uid) == 0
    assert await _count_bare_persons() == 0
    # the contribution landed on the surviving person
    assert await _count_contributions_between(document.uid, surviving_person.uid) == 1
    # every contributor of the record got a contribution
    assert await _count_document_contributions(document.uid) == len(linked_people)


async def test_contribution_mapping_skips_unresolvable_person(
        persisted_person_a_pydantic_model: Person,  # pylint: disable=unused-argument
        hal_article_a_source_record_persisted_model: SourceRecord,
) -> None:
    """
    Given a linked person that no longer exists and cannot be re-resolved
    When the contributions are written
    Then the contribution is skipped without error and no bare Person node is created
    """
    source_record = hal_article_a_source_record_persisted_model
    document = await _create_document_for_source_record(source_record)
    service = SourceContributorMappingService(
        source_records=[source_record], document_uid=document.uid)

    async def _unresolvable(_cluster):
        return None

    # pylint: disable=protected-access
    service._resolve_cluster = _unresolvable
    ghost_cluster = [source_record.contributions[0].contributor]
    await service._update_contributions({"ghost-person": ghost_cluster})

    assert await _count_persons_by_uid("ghost-person") == 0
    assert await _count_bare_persons() == 0
    assert await _count_document_contributions(document.uid) == 0


async def test_merge_external_people_preserves_contributions() -> None:
    """
    Given person A with contributions on documents D1 and D2,
    and person B with a contribution on D1 only
    When A is merged into B
    Then B holds one contribution on each document, the D1 duplicate is removed,
    and no contribution is orphaned
    """
    person_dao = _person_dao()
    document_dao = _document_dao()
    person_a = Person(uid="hal-ext-author", display_name="Ext Author", external=True)
    person_b = Person(uid="scanr-ext-author", display_name="Ext Author", external=True)
    await person_dao.create(person_a)
    await person_dao.create(person_b)
    await document_dao.create_or_update_document(Document(uid="doc-merge-1"))
    await document_dao.create_or_update_document(Document(uid="doc-merge-2"))
    assert await document_dao.create_contribution(
        "doc-merge-1", person_a.uid, roles=[AUTHOR_ROLE]) is not None
    assert await document_dao.create_contribution(
        "doc-merge-2", person_a.uid, roles=[AUTHOR_ROLE]) is not None
    assert await document_dao.create_contribution(
        "doc-merge-1", person_b.uid, roles=[AUTHOR_ROLE]) is not None

    await person_dao.merge_people(person_b.uid, person_a.uid)

    assert await _count_persons_by_uid(person_a.uid) == 0
    assert await _count_contributions_between("doc-merge-1", person_b.uid) == 1
    assert await _count_contributions_between("doc-merge-2", person_b.uid) == 1
    assert await _count_document_contributions("doc-merge-1") == 1
    assert await _count_document_contributions("doc-merge-2") == 1
    assert await _count_orphan_contributions() == 0


async def test_merge_external_people_transfers_recorded_by() -> None:
    """
    Given a merged person recorded by a source person
    When the person is merged into a survivor
    Then the RECORDED_BY relation is transferred to the survivor
    """
    person_dao = _person_dao()
    person_a = Person(uid="hal-ext-recorded", display_name="Ext Recorded", external=True)
    person_b = Person(uid="scanr-ext-recorded", display_name="Ext Recorded", external=True)
    await person_dao.create(person_a)
    await person_dao.create(person_b)
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            await session.run(
                "CREATE (sp:SourcePerson {uid: 'hal-sp-recorded'}) "
                "WITH sp MATCH (p:Person {uid: 'hal-ext-recorded'}) "
                "CREATE (p)-[:RECORDED_BY]->(sp)")

    await person_dao.merge_people(person_b.uid, person_a.uid)

    assert await _run_count_query(
        "MATCH (:Person {uid: 'scanr-ext-recorded'})-[r:RECORDED_BY]->"
        "(:SourcePerson {uid: 'hal-sp-recorded'}) RETURN count(r) AS count") == 1
    assert await _count_persons_by_uid(person_a.uid) == 0


def test_external_people_merge_survivor_election_is_deterministic() -> None:
    """
    Given a set of external person uids from different sources
    When the merge survivor is elected
    Then the election follows the harvester priority order regardless of input order,
    with unknown prefixes last and lexicographic tie-break
    """
    service = SourceContributorMappingService(source_records=[], document_uid="none")
    # pylint: disable=protected-access
    uids = ["openalex-https://openalex.org/A5041561153", "scanr-idref174365020", "hal-170517"]
    for permutation in permutations(uids):
        elected = sorted(permutation, key=service._survivor_election_key)[0]
        assert elected == "hal-170517"
    # unknown source prefixes sort after known ones
    assert sorted(["sudoc-http://www.idref.fr/174365020/id", "openalex-x"],
                  key=service._survivor_election_key)[0] == "openalex-x"
    # lexicographic tie-break within the same source
    assert sorted(["hal-2", "hal-1"], key=service._survivor_election_key)[0] == "hal-1"
