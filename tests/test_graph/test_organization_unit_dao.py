from collections import Counter

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.organization_unit_dao import OrganizationUnitDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.identifier_types import OrganizationIdentifierType
from app.models.organization_types import (
    GenericOrganizationType,
    MissionType,
    NationalOrganizationType,
    OrgMembershipPosition,
)
from app.models.organization_unit import (
    Institution,
    InstitutionSubdivision,
    OrganizationBase,
    ResearchUnit,
)


def _get_dao() -> OrganizationUnitDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return factory.get_dao(OrganizationBase)


async def _node_labels(uid: str) -> set[str]:
    """Return the set of Neo4j labels for the node with the given uid."""
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    "MATCH (o:OrganizationUnit {uid: $uid}) RETURN labels(o) AS labels",
                    uid=uid,
                )
                record = await result.single()
                return set(record["labels"]) if record else set()


async def _relationship_exists(from_uid: str, rel_type: str, to_uid: str) -> dict | None:
    """Return relationship properties if it exists, else None."""
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    f"MATCH (a:OrganizationUnit {{uid: $from_uid}})-[r:{rel_type}]->"
                    "(b:OrganizationUnit {uid: $to_uid}) RETURN properties(r) AS props",
                    from_uid=from_uid,
                    to_uid=to_uid,
                )
                record = await result.single()
                return dict(record["props"]) if record else None


async def _person_relationship_exists(person_uid: str, org_uid: str) -> bool:
    """Check if a Person-[:MEMBER_OF]->OrganizationUnit relationship exists."""
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    "MATCH (:Person {uid: $person_uid})-[:MEMBER_OF]->"
                    "(:OrganizationUnit {uid: $org_uid}) RETURN count(*) AS cnt",
                    person_uid=person_uid,
                    org_uid=org_uid,
                )
                record = await result.single()
                return record["cnt"] > 0 if record else False


async def _create_person_member_of_org(person_uid: str, org_uid: str):
    """Manually create a (:Person)-[:MEMBER_OF]->(:OrganizationUnit) relationship."""
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                await tx.run(
                    "MERGE (p:Person {uid: $person_uid}) "
                    "WITH p "
                    "MATCH (o:OrganizationUnit {uid: $org_uid}) "
                    "MERGE (p)-[:MEMBER_OF]->(o)",
                    person_uid=person_uid,
                    org_uid=org_uid,
                )


async def test_create_research_unit(
        test_app,
        research_unit_center_pydantic_model: OrganizationBase,
        caplog,
):
    dao = _get_dao()
    await dao.create(research_unit_center_pydantic_model)

    uid = research_unit_center_pydantic_model.uid
    assert uid == "local-CENTER-001"

    # Verify labels in the graph
    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Unit" in labels
    assert "ResearchUnit" in labels

    # Retrieve and assert Pydantic fields
    retrieved = await dao.get(uid)
    assert retrieved is not None
    assert isinstance(retrieved, ResearchUnit)
    assert retrieved.uid == uid
    assert retrieved.generic_type == GenericOrganizationType.UNIT
    assert retrieved.national_type == NationalOrganizationType.UMR
    assert retrieved.main_mission == MissionType.RESEARCH

    assert len(retrieved.long_labels) == 2
    assert any(ll.value == "Example Research Center" for ll in retrieved.long_labels)
    assert len(retrieved.short_labels) == 1
    assert retrieved.short_labels[0].value == "ERC"

    assert len(retrieved.local_types) == 2
    assert any(lt.value == "Center" for lt in retrieved.local_types)

    assert len(retrieved.identifiers) == 3
    id_map = {i.type.value: i.value for i in retrieved.identifiers}
    assert id_map["local"] == "CENTER-001"
    assert id_map["nns"] == "NNS-EXAMPLE"
    assert id_map["ror"] == "ROR-EXAMPLE"

    # MEMBER_OF not created because institution doesn't exist
    assert len(retrieved.memberships) == 0
    assert any("not found" in msg.lower() or "target" in msg.lower() for msg in caplog.messages)


async def test_create_institution(
        test_app,
        institution_a_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(institution_a_pydantic_model)

    uid = institution_a_pydantic_model.uid
    assert uid == "local-EXAMPLE-UNIV-001"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Institution" in labels
    assert "ResearchUnit" not in labels

    retrieved = await dao.get(uid)
    assert retrieved is not None
    assert isinstance(retrieved, Institution)
    assert len(retrieved.long_labels) == 2
    assert len(retrieved.short_labels) == 2
    assert retrieved.national_type == NationalOrganizationType.UNIV


async def test_create_institution_subdivision_with_part_of(
        test_app,
        persisted_institution_a_pydantic_model: OrganizationBase,
        institution_subdivision_a_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(institution_subdivision_a_pydantic_model)

    fac_uid = institution_subdivision_a_pydantic_model.uid
    assert fac_uid == "local-FAC-EXAMPLE-001"

    labels = await _node_labels(fac_uid)
    assert "InstitutionSubdivision" in labels

    # Verify PART_OF relationship
    rel_props = await _relationship_exists(fac_uid, "PART_OF", "local-EXAMPLE-UNIV-001")
    assert rel_props is not None
    assert str(rel_props["start_date"]) == "2010-01-01"
    assert str(rel_props["end_date"]) == "2030-12-31"

    retrieved = await dao.get(fac_uid)
    assert retrieved is not None
    assert isinstance(retrieved, InstitutionSubdivision)
    assert len(retrieved.parents) == 1
    assert retrieved.parents[0].target == "local-EXAMPLE-UNIV-001"


async def test_create_research_unit_with_member_of(
        test_app,
        persisted_institution_a_pydantic_model: OrganizationBase,
        research_unit_center_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(research_unit_center_pydantic_model)

    ru_uid = research_unit_center_pydantic_model.uid

    rel_props = await _relationship_exists(ru_uid, "MEMBER_OF", "local-EXAMPLE-UNIV-001")
    assert rel_props is not None
    assert rel_props["position"] == OrgMembershipPosition.MAIN_SUPERVISION.value
    assert str(rel_props["start_date"]) == "2000-01-01"
    assert rel_props.get("end_date") is None

    retrieved = await dao.get(ru_uid)
    assert len(retrieved.memberships) == 1
    m = retrieved.memberships[0]
    assert m.target == "local-EXAMPLE-UNIV-001"
    assert m.position == OrgMembershipPosition.MAIN_SUPERVISION


async def test_create_research_unit_missing_parent_does_not_raise(
        test_app,
        research_unit_center_pydantic_model: OrganizationBase,
        caplog,
):
    dao = _get_dao()
    # Institution not created — MEMBER_OF target is missing
    await dao.create(research_unit_center_pydantic_model)

    ru_uid = research_unit_center_pydantic_model.uid
    assert ru_uid is not None

    rel_props = await _relationship_exists(ru_uid, "MEMBER_OF", "local-EXAMPLE-UNIV-001")
    assert rel_props is None  # relationship not created

    assert any("not found" in msg.lower() or "target" in msg.lower() for msg in caplog.messages)


async def test_update_research_unit_replaces_labels(
        test_app,
        persisted_research_unit_center_pydantic_model: OrganizationBase,
        research_unit_center_updated_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    uid = persisted_research_unit_center_pydantic_model.uid

    await dao.update(research_unit_center_updated_pydantic_model)

    retrieved = await dao.get(uid)
    assert retrieved is not None

    # Old labels gone, new ones present
    assert len(retrieved.short_labels) == 1
    assert retrieved.short_labels[0].value == "UERC"
    assert not any(sl.value == "ERC" for sl in retrieved.short_labels)

    assert len(retrieved.long_labels) == 1
    assert retrieved.long_labels[0].value == "Updated Example Research Center"

    # NNS identifier removed, ROR and LOCAL remain
    id_map = {i.type.value: i.value for i in retrieved.identifiers}
    assert "local" in id_map
    assert "ror" in id_map
    assert "nns" not in id_map

    # local_types updated
    assert len(retrieved.local_types) == 1
    assert retrieved.local_types[0].value == "Research Center"


async def test_update_research_unit_removes_org_relationships(
        test_app,
        persisted_institution_a_pydantic_model: OrganizationBase,
        research_unit_center_pydantic_model: OrganizationBase,
        research_unit_center_updated_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    # Create the research unit (will get MEMBER_OF → institution)
    await dao.create(research_unit_center_pydantic_model)
    ru_uid = research_unit_center_pydantic_model.uid

    rel_before = await _relationship_exists(ru_uid, "MEMBER_OF", "local-EXAMPLE-UNIV-001")
    assert rel_before is not None

    # Update with no relationships
    await dao.update(research_unit_center_updated_pydantic_model)

    rel_after = await _relationship_exists(ru_uid, "MEMBER_OF", "local-EXAMPLE-UNIV-001")
    assert rel_after is None


async def test_unchanged_event_creates_new(
        test_app,
        research_unit_center_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    uid, status = await dao.create_or_update(research_unit_center_pydantic_model)
    assert uid == "local-CENTER-001"
    assert status == OrganizationUnitDAO.Status.CREATED

    retrieved = await dao.get(uid)
    assert retrieved is not None


async def test_unchanged_event_updates_existing(
        test_app,
        persisted_research_unit_center_pydantic_model: OrganizationBase,
        research_unit_center_updated_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    uid, status = await dao.create_or_update(research_unit_center_updated_pydantic_model)
    assert uid == "local-CENTER-001"
    assert status == OrganizationUnitDAO.Status.UPDATED

    retrieved = await dao.get(uid)
    assert retrieved.short_labels[0].value == "UERC"


async def test_update_preserves_person_to_structure_relationship(
        test_app,
        persisted_research_unit_center_pydantic_model: OrganizationBase,
        research_unit_center_updated_pydantic_model: OrganizationBase,
):
    ru_uid = persisted_research_unit_center_pydantic_model.uid
    person_uid = "test-person-001"

    # Manually create Person → OrganizationUnit MEMBER_OF
    await _create_person_member_of_org(person_uid, ru_uid)
    assert await _person_relationship_exists(person_uid, ru_uid)

    dao = _get_dao()
    await dao.update(research_unit_center_updated_pydantic_model)

    # Person relationship must still exist after update
    assert await _person_relationship_exists(person_uid, ru_uid)
