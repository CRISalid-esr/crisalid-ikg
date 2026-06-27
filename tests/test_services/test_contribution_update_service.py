# file: tests/test_services/test_contribution_update_service.py
from unittest.mock import patch, AsyncMock

import pytest

from app.amqp.message_mode import MessageMode
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.change import Change, TargetType, ChangeStatus
from app.models.document import Document
from app.models.people import Person
from app.services.changes.change_processor_factory import ChangeProcessorFactory
from app.services.changes.change_service import ChangeService
from app.services.changes.processors.document_contributions_change_processor import \
    DocumentContributionsChangeProcessor

AUT = "http://id.loc.gov/vocabulary/relators/aut"
CTB = "http://id.loc.gov/vocabulary/relators/ctb"


@pytest.fixture(name="mocked_document_updated_signal")
def mocked_document_updated_signal_fixture():
    """Mock the `document_updated` signal."""
    with patch("app.signals.document_updated.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


def _contributions_change(document_uid: str, contributions: list[dict],
                          uid: str = "sovisuplus:c1",
                          change_id: str = "c1",
                          timestamp: str = "2026-01-01T09:00:00Z") -> Change:
    return Change(
        uid=uid,
        target_uid=document_uid,
        target_type=TargetType.DOCUMENT,
        person_uid="local-user1",
        application="sovisuplus",
        id=change_id,
        action_type="UPDATE",
        path="contributions",
        parameters={"contributions": contributions},
        timestamp=timestamp,
    )


async def _contributor_uids(document_uid: str) -> set:
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_uid(document_uid)
    return {contribution.contributor.uid for contribution in document.contributions}


async def _count_affiliation_statements(document_uid: str) -> int:
    query = (
        "MATCH (:Document {uid: $uid})-[:HAS_CONTRIBUTION]->(:Contribution)"
        "-[r:HAS_AFFILIATION_STATEMENT]->(:AuthorityOrganization) RETURN count(r) AS n"
    )
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, uid=document_uid)
            record = await result.single()
            return record["n"]


def test_factory_routes_contributions_to_processor() -> None:
    """The factory routes a path=contributions document change to the new processor."""
    change = _contributions_change("doc-1", [])
    processor = ChangeProcessorFactory.get_processor(change)
    assert isinstance(processor, DocumentContributionsChangeProcessor)


@pytest.mark.asyncio
async def test_reconcile_replaces_contributions(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:
    """
    Given a persisted document and an internal person,
    When a full-state contributions change is applied with the internal person (by uid),
        a brand-new external person (uid null) and an affiliation,
    Then the document's contributors are exactly the submitted ones and affiliations are linked.
    """
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model

    contributions = [
        {
            "rank": 0,
            "roles": [AUT],
            "person": {"uid": internal.uid, "displayName": internal.display_name,
                       "identifiers": []},
            "affiliations": [
                {"hal": "1000001", "idref": "100000001", "ror": None, "isni": None,
                 "nns": None, "wikidata": None, "name": "Example University",
                 "label": "Example University [EU]", "acronym": "EU", "type": "institution"}
            ],
        },
        {
            "rank": 1,
            "roles": [CTB],
            "person": {"uid": None, "displayName": "Claire Durand",
                       "firstName": "Claire", "lastName": "Durand",
                       "identifiers": [{"type": "orcid", "value": "0000-0000-0000-0002"}]},
            "affiliations": [],
        },
    ]
    change = _contributions_change(document.uid, contributions)

    await ChangeService().create_and_apply_change(change)

    contributor_uids = await _contributor_uids(document.uid)
    assert internal.uid in contributor_uids
    assert "orcid-0000-0000-0000-0002" in contributor_uids
    assert len(contributor_uids) == 2
    assert await _count_affiliation_statements(document.uid) >= 1

    mocked_document_updated_signal.assert_called_once()
    assert mocked_document_updated_signal.call_args.kwargs == {
        "document_uid": document.uid, "mode": MessageMode.INTERACTIVE}


@pytest.mark.asyncio
async def test_empty_list_removes_all_contributors(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """An empty contributions list removes all the document's contributors."""
    document = document_hal_article_a_persisted_model
    change = _contributions_change(document.uid, [])

    await ChangeService().create_and_apply_change(change)

    assert await _contributor_uids(document.uid) == set()


@pytest.mark.asyncio
async def test_internal_person_identifiers_are_frozen(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """
    Incoming identifiers for an internal person are ignored (frozen): no AgentIdentifier added.
    """
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model
    person_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Person)
    before = {(i.type.value, i.value) for i in (await person_dao.get(internal.uid)).identifiers}

    contributions = [{
        "rank": 0,
        "roles": [AUT],
        "person": {"uid": internal.uid, "displayName": internal.display_name,
                   "identifiers": [{"type": "idref", "value": "999999999"}]},
        "affiliations": [],
    }]
    await ChangeService().create_and_apply_change(
        _contributions_change(document.uid, contributions))

    after = {(i.type.value, i.value) for i in (await person_dao.get(internal.uid)).identifiers}
    assert after == before
    assert ("idref", "999999999") not in after


@pytest.mark.asyncio
async def test_supersession_only_latest_contributions_change_replayed(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """
    On replay, only the latest contributions change is applied; older ones are kept but skipped.
    """
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model
    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)

    older = _contributions_change(
        document.uid,
        [{"rank": 0, "roles": [AUT],
          "person": {"uid": internal.uid, "displayName": internal.display_name,
                     "identifiers": []},
          "affiliations": []}],
        uid="sovisuplus:old", change_id="old", timestamp="2026-01-01T08:00:00Z")
    newer = _contributions_change(
        document.uid,
        [{"rank": 0, "roles": [AUT],
          "person": {"uid": internal.uid, "displayName": internal.display_name,
                     "identifiers": []},
          "affiliations": []}],
        uid="sovisuplus:new", change_id="new", timestamp="2026-01-02T08:00:00Z")
    await change_dao.create_document_change(document, older)
    await change_dao.create_document_change(document, newer)

    await ChangeService().apply_changes_to_node(document.uid, mode=MessageMode.BATCH)

    assert (await change_dao.get_by_uid("sovisuplus:new")).status == ChangeStatus.APPLIED
    # older change is superseded: not applied, but preserved in the graph
    stored_older = await change_dao.get_by_uid("sovisuplus:old")
    assert stored_older is not None
    assert stored_older.status == ChangeStatus.CREATED


@pytest.mark.asyncio
async def test_reconcile_resolves_existing_external_person_by_uid(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """
    An existing external person (display_name only, no PersonName) referenced by uid is
    resolved without a hydration failure (regression: _hydrate dropped display_name).
    """
    document = document_hal_article_a_persisted_model
    person_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Person)
    external = Person(uid="orcid-0000-0002-7428-4208", display_name="Bernard Chevalier",
                      external=True,
                      identifiers=[{"type": "orcid", "value": "0000-0002-7428-4208"}])
    await person_dao.create(external)

    # get() must hydrate the external person without raising
    hydrated = await person_dao.get(external.uid)
    assert hydrated is not None
    assert hydrated.display_name == "Bernard Chevalier"
    assert hydrated.external is True

    contributions = [{
        "rank": 1, "roles": [CTB],
        "person": {"uid": external.uid, "displayName": "Bernard Chevalier",
                   "firstName": None, "lastName": None,
                   "identifiers": [{"type": "orcid", "value": "0000-0002-7428-4208"}]},
        "affiliations": [],
    }]
    await ChangeService().create_and_apply_change(
        _contributions_change(document.uid, contributions))

    assert external.uid in await _contributor_uids(document.uid)


@pytest.mark.asyncio
async def test_replay_emits_batch_mode(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:
    """Replaying a contributions change via apply_changes_to_node emits BATCH mode."""
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model
    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    change = _contributions_change(
        document.uid,
        [{"rank": 0, "roles": [AUT],
          "person": {"uid": internal.uid, "displayName": internal.display_name,
                     "identifiers": []},
          "affiliations": []}])
    await change_dao.create_document_change(document, change)

    await ChangeService().apply_changes_to_node(document.uid, mode=MessageMode.BATCH)

    assert mocked_document_updated_signal.call_args is not None
    assert mocked_document_updated_signal.call_args.kwargs["mode"] == MessageMode.BATCH
