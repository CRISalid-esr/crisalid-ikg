# file: tests/test_services/test_affiliation_type_update.py
"""
Issue #415: a user-submitted affiliation type must be applied to the shared authority
state and protected from later harvest overwrite (see specs/affiliations-type-update-...).
"""
import copy
from unittest.mock import patch, AsyncMock

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.authority_organization_dao import AuthorityOrganizationDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.agent_identifiers import OrganizationIdentifier, PersonIdentifier
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.change import Change, TargetType
from app.models.document import Document
from app.models.harvesting_sources import HarvestingSource
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.people import Person
from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.source_organizations import SourceOrganization
from app.models.source_records import SourceRecord
from app.services.authority_organizations.authority_organization_service import \
    AuthorityOrganizationService
from app.services.changes.change_service import ChangeService
from app.services.documents.document_service import DocumentService
from app.services.source_records.source_record_service import SourceRecordService

AUT = "http://id.loc.gov/vocabulary/relators/aut"
OrgType = SourceOrganization.SourceOrganisationType
TypeOrigin = AuthorityOrganizationState.TypeOrigin

# HAL structId of "Université Anonyme" in hal_chapter_a_source_record.json (type institution)
CHAPTER_STRUCT_ID = "2001"


@pytest.fixture(name="mocked_document_updated_signal")
def mocked_document_updated_signal_fixture():
    """Mock the `document_updated` signal."""
    with patch("app.signals.document_updated.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


def _contributions_change(document_uid: str, person: Person, affiliation: dict,
                          change_id: str = "c1",
                          timestamp: str = "2026-01-01T09:00:00Z") -> Change:
    return Change(
        uid=f"sovisuplus:{change_id}",
        target_uid=document_uid,
        target_type=TargetType.DOCUMENT,
        person_uid="local-user1",
        application="sovisuplus",
        id=change_id,
        action_type="UPDATE",
        path="contributions",
        parameters={"contributions": [{
            "rank": 0, "roles": [AUT],
            "person": {"uid": person.uid, "displayName": person.display_name,
                       "identifiers": []},
            "affiliations": [affiliation],
        }]},
        timestamp=timestamp,
    )


def _hal_affiliation(struct_id: str = CHAPTER_STRUCT_ID, **overrides) -> dict:
    affiliation = {"hal": struct_id, "idref": None, "ror": None, "isni": None, "nns": None,
                   "wikidata": None, "name": "Université Anonyme",
                   "label": "Université Anonyme", "acronym": None, "type": "institution"}
    affiliation.update(overrides)
    return affiliation


async def _state_by_hal_id(struct_id: str) -> AuthorityOrganizationState:
    query = (
        "MATCH (o:AuthorityOrganizationState)-[:HAS_IDENTIFIER]->"
        "(i:AgentIdentifier {type: 'hal', value: $value}) RETURN o.uid AS uid"
    )
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, value=struct_id)
            uids = [record["uid"] async for record in result]
    assert len(uids) == 1, f"expected exactly one state for hal {struct_id}, got {uids}"
    return await _dao().get_authority_organization_state_by_uid(uids[0])


async def _affiliation_target_uids(document_uid: str) -> set:
    query = (
        "MATCH (:Document {uid: $uid})-[:HAS_CONTRIBUTION]->(:Contribution)"
        "-[:HAS_AFFILIATION_STATEMENT]->(o:AuthorityOrganization) RETURN collect(o.uid) AS uids"
    )
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(query, uid=document_uid)
            return set((await result.single())["uids"])


async def _document_of(source_record: SourceRecord) -> Document:
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_source_record_uid(source_record.uid)
    assert document is not None
    return document


def _dao() -> AuthorityOrganizationDAO:
    return AbstractDAOFactory().get_dao_factory("neo4j").get_dao(AuthorityOrganizationState)


def _hal_source_org(struct_id: str, org_type: OrgType, name: str) -> SourceOrganization:
    return SourceOrganization(
        source=HarvestingSource.HAL, source_identifier=struct_id, name=name, type=org_type,
        identifiers=[SourceOrganizationIdentifier(
            type=OrganizationIdentifierType.HAL.value, value=struct_id)])


async def _apply(change: Change) -> Change:
    await ChangeService().create_and_apply_change(change)
    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    return await change_dao.get_by_uid(change.uid)


# ------------------------------------------------------------------ 1. model & persistence

def test_type_origin_defaults_to_harvest() -> None:
    """A state built without provenance is harvest-typed."""
    assert AuthorityOrganizationState().type_origin == TypeOrigin.HARVEST


@pytest.mark.asyncio
async def test_type_origin_round_trips_and_hydrates_to_harvest_when_missing(
        test_app) -> None:  # pylint: disable=unused-argument
    """A user origin is persisted and read back; a node without the property hydrates to harvest."""
    dao = _dao()
    state = AuthorityOrganizationState(
        type=OrgType.LABORATORY, type_origin=TypeOrigin.USER,
        identifiers=[OrganizationIdentifier(type=OrganizationIdentifierType.HAL, value="9001")])
    state.set_names([Literal(value="Lab 9001")])
    created = await dao.create_authority_organization_state(state)

    fetched = await dao.get_authority_organization_state_by_uid(created.uid)
    assert fetched.type == OrgType.LABORATORY
    assert fetched.type_origin == TypeOrigin.USER

    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            await session.run(
                "MATCH (o:AuthorityOrganizationState {uid: $uid}) REMOVE o.type_origin",
                uid=created.uid)
    fetched = await dao.get_authority_organization_state_by_uid(created.uid)
    assert fetched.type_origin == TypeOrigin.HARVEST


# ------------------------------------------------------------------ 2. user override

@pytest.mark.asyncio
async def test_user_type_overrides_harvested_type(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """A user-submitted type replaces the harvested type and marks the state as user-typed."""
    before = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert before.type == OrgType.INSTITUTION
    assert before.type_origin == TypeOrigin.HARVEST

    document = await _document_of(hal_chapter_a_source_record_persisted_model)
    await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model, _hal_affiliation(type="laboratory")))

    after = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert after.uid == before.uid
    assert after.type == OrgType.LABORATORY
    assert after.type_origin == TypeOrigin.USER
    assert after.uid in await _affiliation_target_uids(document.uid)


# ------------------------------------------------------------------ 3. cross-document harvest

@pytest.mark.asyncio
async def test_harvest_of_another_document_keeps_user_type(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        hal_chapter_a_source_record_json_data: dict,
        persisted_person_a_pydantic_model: Person,
        default_identifier_used: PersonIdentifier,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """
    After a user retyped the structure from document A, harvesting document B affiliated
    to the same structure (with the HAL type) does not revert the shared state's type.
    """
    document_a = await _document_of(hal_chapter_a_source_record_persisted_model)
    await _apply(_contributions_change(
        document_a.uid, persisted_person_a_pydantic_model, _hal_affiliation(type="laboratory")))
    state = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert state.type == OrgType.LABORATORY

    other_data = copy.deepcopy(hal_chapter_a_source_record_json_data)
    other_data["source_identifier"] = "hal-00000002"
    other_data["identifiers"] = [{"type": "hal", "value": "hal-00000002"}]
    other_data["titles"] = [{"value": "Un autre chapitre sur le CLOUD", "language": "fr"}]
    other_record = SourceRecord(**other_data)
    service = SourceRecordService()
    await service.create_source_record(
        source_record=other_record, harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)
    document_b = await _document_of(await service.get_source_record(other_record.uid))
    assert document_b.uid != document_a.uid

    after = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert after.uid == state.uid
    assert after.type == OrgType.LABORATORY
    assert after.type_origin == TypeOrigin.USER
    assert after.uid in await _affiliation_target_uids(document_a.uid)
    assert after.uid in await _affiliation_target_uids(document_b.uid)


# ------------------------------------------------------------------ 4. same-document replay

@pytest.mark.asyncio
async def test_recomputation_of_same_document_keeps_user_type(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """Recomputing the edited document (harvest path then change replay) keeps the user type."""
    document = await _document_of(hal_chapter_a_source_record_persisted_model)
    await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model, _hal_affiliation(type="laboratory")))

    await DocumentService().update_from_source_records(None, document.uid)

    after = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert after.type == OrgType.LABORATORY
    assert after.type_origin == TypeOrigin.USER


# ------------------------------------------------------------------ 5. harvest rule unchanged

@pytest.mark.asyncio
async def test_harvest_fills_generic_type_only(
        test_app) -> None:  # pylint: disable=unused-argument
    """Harvest sets a type on a generic state but never replaces a real harvested type."""
    service = AuthorityOrganizationService()
    root = await service.get_or_create_authority_organization(
        [_hal_source_org("8001", OrgType.ORGANIZATION, "Structure 8001")])
    state_uid = root.states[0].uid
    assert (await _state_by_hal_id("8001")).type == OrgType.ORGANIZATION

    await service.get_or_create_authority_organization(
        [_hal_source_org("8001", OrgType.LABORATORY, "Structure 8001")])
    state = await _state_by_hal_id("8001")
    assert state.uid == state_uid
    assert state.type == OrgType.LABORATORY
    assert state.type_origin == TypeOrigin.HARVEST

    await service.get_or_create_authority_organization(
        [_hal_source_org("8001", OrgType.INSTITUTION, "Structure 8001")])
    state = await _state_by_hal_id("8001")
    assert state.type == OrgType.LABORATORY
    assert state.type_origin == TypeOrigin.HARVEST


# ------------------------------------------------------------------ 6. unknown / missing type

@pytest.mark.asyncio
@pytest.mark.parametrize("raw_type", [None, "foo"])
async def test_missing_or_unknown_type_does_not_override(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal,  # pylint: disable=unused-argument
        raw_type) -> None:
    """A null or unmapped type leaves the harvested type untouched; unmapped values are reported."""
    document = await _document_of(hal_chapter_a_source_record_persisted_model)
    stored = await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model, _hal_affiliation(type=raw_type)))

    state = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert state.type == OrgType.INSTITUTION
    assert state.type_origin == TypeOrigin.HARVEST
    codes = [warning.code for warning in stored.warnings]
    if raw_type is None:
        assert "AFFILIATION_TYPE_UNKNOWN" not in codes
    else:
        assert "AFFILIATION_TYPE_UNKNOWN" in codes


# ------------------------------------------------------------------ 7. department

@pytest.mark.asyncio
async def test_department_type_is_supported(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """The HAL `department` type is mapped and persisted."""
    document = await _document_of(hal_chapter_a_source_record_persisted_model)
    await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model, _hal_affiliation(type="department")))

    state = await _state_by_hal_id(CHAPTER_STRUCT_ID)
    assert state.type == OrgType.DEPARTMENT
    assert state.type_origin == TypeOrigin.USER


# ------------------------------------------------------------------ 8. names preserved

@pytest.mark.asyncio
async def test_user_affiliation_preserves_state_names(
        test_app,  # pylint: disable=unused-argument
        hal_chapter_a_source_record_persisted_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal) -> None:  # pylint: disable=unused-argument
    """A user affiliation adds its name to the state and never removes harvested names."""
    document = await _document_of(hal_chapter_a_source_record_persisted_model)
    harvested_names = set((await _state_by_hal_id(CHAPTER_STRUCT_ID)).display_names)
    assert "Université Anonyme" in harvested_names

    await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model,
        _hal_affiliation(type="laboratory", name="Univ. Anonyme", label="Univ. Anonyme"),
        change_id="c1"))
    names = set((await _state_by_hal_id(CHAPTER_STRUCT_ID)).display_names)
    assert names == harvested_names | {"Univ. Anonyme"}

    await _apply(_contributions_change(
        document.uid, persisted_person_a_pydantic_model,
        _hal_affiliation(type="laboratory", name=None, label=None),
        change_id="c2", timestamp="2026-01-01T10:00:00Z"))
    assert set((await _state_by_hal_id(CHAPTER_STRUCT_ID)).display_names) == names
