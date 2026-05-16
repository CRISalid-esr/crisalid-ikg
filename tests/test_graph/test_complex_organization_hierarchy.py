from datetime import date

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.organization_unit_dao import OrganizationUnitDAO
from app.models.organization_types import NationalOrganizationType
from app.models.organization_unit import OrganizationBase


def _get_dao() -> OrganizationUnitDAO:
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    return factory.get_dao(OrganizationBase)


async def _node_labels(uid: str) -> set[str]:
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


async def test_create_epe_institution(
        test_app,
        epe_paris_sud_ouest_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(epe_paris_sud_ouest_pydantic_model)

    uid = epe_paris_sud_ouest_pydantic_model.uid
    assert uid == "uai-07890"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Institution" in labels
    assert "Unit" not in labels

    assert epe_paris_sud_ouest_pydantic_model.national_type == NationalOrganizationType.EPE
    assert any(ll.value == "Université Paris Sud-Ouest"
               for ll in epe_paris_sud_ouest_pydantic_model.long_labels)


async def test_create_univ_member_of_epe(
        test_app,
        persisted_epe_paris_sud_ouest_pydantic_model: OrganizationBase,
        univ_etienne_dupond_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(univ_etienne_dupond_pydantic_model)

    uid = univ_etienne_dupond_pydantic_model.uid
    assert uid == "uai-02345"

    rel = await _relationship_exists("uai-02345", "MEMBER_OF", "uai-07890")
    assert rel is not None
    assert rel.get("start_date") == date(2020, 1, 1)


async def test_create_cnrs_epst_institution(
        test_app,
        cnrs_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(cnrs_pydantic_model)

    uid = cnrs_pydantic_model.uid
    assert uid == "uai-0757581P"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Institution" in labels
    assert cnrs_pydantic_model.national_type == NationalOrganizationType.EPST
    assert any(sl.value == "CNRS" for sl in cnrs_pydantic_model.short_labels)


async def test_create_ena_ge_institution(
        test_app,
        ena_astrophysique_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(ena_astrophysique_pydantic_model)

    uid = ena_astrophysique_pydantic_model.uid
    assert uid == "uai-0123456A"

    labels = await _node_labels(uid)
    assert "Institution" in labels
    assert ena_astrophysique_pydantic_model.national_type == NationalOrganizationType.GE


async def test_create_dept_physique_part_of_univ(
        test_app,
        persisted_univ_etienne_dupond_pydantic_model: OrganizationBase,
        dept_physique_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(dept_physique_pydantic_model)

    uid = dept_physique_pydantic_model.uid
    assert uid == "local-DEPT-PHY-001"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "InstitutionSubdivision" in labels

    rel = await _relationship_exists("local-DEPT-PHY-001", "PART_OF", "uai-02345")
    assert rel is not None
    assert rel.get("start_date") == date(1995, 1, 1)


async def test_create_fac_sciences_part_of_univ(
        test_app,
        persisted_univ_etienne_dupond_pydantic_model: OrganizationBase,
        fac_sciences_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(fac_sciences_pydantic_model)

    uid = fac_sciences_pydantic_model.uid
    assert uid == "local-FAC-SCI-001"

    rel = await _relationship_exists("local-FAC-SCI-001", "PART_OF", "uai-02345")
    assert rel is not None
    assert rel.get("start_date") == date(1995, 1, 1)


async def test_create_lra_with_full_supervision_chain(
        test_app,
        persisted_univ_etienne_dupond_pydantic_model: OrganizationBase,
        persisted_cnrs_pydantic_model: OrganizationBase,
        persisted_ena_astrophysique_pydantic_model: OrganizationBase,
        persisted_dept_physique_pydantic_model: OrganizationBase,
        persisted_fac_sciences_pydantic_model: OrganizationBase,
        lra_research_unit_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(lra_research_unit_pydantic_model)

    uid = lra_research_unit_pydantic_model.uid
    assert uid == "local-123456"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Unit" in labels
    assert "ResearchUnit" in labels

    main_rel = await _relationship_exists("local-123456", "MEMBER_OF", "uai-02345")
    assert main_rel is not None
    assert main_rel.get("position") == "main_supervision"
    assert main_rel.get("start_date") == date(2000, 1, 1)

    cnrs_rel = await _relationship_exists("local-123456", "MEMBER_OF", "uai-0757581P")
    assert cnrs_rel is not None
    assert cnrs_rel.get("position") == "associated_supervision"

    ena_rel = await _relationship_exists("local-123456", "MEMBER_OF", "uai-0123456A")
    assert ena_rel is not None
    assert ena_rel.get("position") == "associated_supervision"
    assert ena_rel.get("start_date") == date(2005, 1, 1)

    dept_rel = await _relationship_exists("local-123456", "MEMBER_OF", "local-DEPT-PHY-001")
    assert dept_rel is not None
    assert dept_rel.get("start_date") == date(2000, 1, 1)

    fac_rel = await _relationship_exists("local-123456", "PART_OF", "local-FAC-SCI-001")
    assert fac_rel is not None
    assert fac_rel.get("start_date") == date(2000, 1, 1)


async def test_create_team_part_of_lra(
        test_app,
        persisted_lra_research_unit_pydantic_model: OrganizationBase,
        team_astrophysique_pydantic_model: OrganizationBase,
        caplog,
):
    dao = _get_dao()
    await dao.create(team_astrophysique_pydantic_model)

    uid = team_astrophysique_pydantic_model.uid
    assert uid == "local-TEAM-ASTRO-001"

    labels = await _node_labels(uid)
    assert "OrganizationUnit" in labels
    assert "Team" in labels

    rel = await _relationship_exists("local-TEAM-ASTRO-001", "PART_OF", "local-123456")
    assert rel is not None
    assert rel.get("start_date") == date(2010, 1, 1)

    # axis not persisted yet — MEMBER_OF should be skipped, not raise
    no_rel = await _relationship_exists("local-TEAM-ASTRO-001", "MEMBER_OF", "local-AXIS-OBS-001")
    assert no_rel is None


async def test_create_axis_and_team_member_of_axis(
        test_app,
        persisted_lra_research_unit_pydantic_model: OrganizationBase,
        axis_observationnel_pydantic_model: OrganizationBase,
        team_astrophysique_pydantic_model: OrganizationBase,
):
    dao = _get_dao()
    await dao.create(axis_observationnel_pydantic_model)
    await dao.create(team_astrophysique_pydantic_model)

    axis_uid = axis_observationnel_pydantic_model.uid
    assert axis_uid == "local-AXIS-OBS-001"

    labels = await _node_labels(axis_uid)
    assert "OrganizationUnit" in labels
    assert "UnitSubdivision" in labels

    axis_rel = await _relationship_exists("local-AXIS-OBS-001", "PART_OF", "local-123456")
    assert axis_rel is not None
    assert axis_rel.get("start_date") == date(2010, 1, 1)

    team_rel = await _relationship_exists("local-TEAM-ASTRO-001", "MEMBER_OF", "local-AXIS-OBS-001")
    assert team_rel is not None
    assert team_rel.get("start_date") == date(2010, 1, 1)
