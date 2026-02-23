# file: tests/test_graph/test_source_organization_dao.py

import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.source_organizations import SourceOrganization


@pytest.mark.asyncio
async def test_create_source_organization(
        hal_source_institution_pydantic_model: SourceOrganization):
    """
    Test creating a SourceOrganization in the graph database.
    :param hal_source_institution_pydantic_model:
    :return:
    """
    dao = _get_source_organization_dao()

    await dao.create(hal_source_institution_pydantic_model)

    so_from_db = await dao.get_by_uid(hal_source_institution_pydantic_model.uid)
    assert so_from_db is not None
    assert so_from_db.uid == hal_source_institution_pydantic_model.uid
    assert so_from_db.source == hal_source_institution_pydantic_model.source
    assert so_from_db.source_identifier == hal_source_institution_pydantic_model.source_identifier
    assert so_from_db.name == hal_source_institution_pydantic_model.name
    assert so_from_db.type == hal_source_institution_pydantic_model.type

    # identifiers persisted
    for ident in hal_source_institution_pydantic_model.identifiers:
        assert any(
            ident.type == ident_db.type and ident.value == ident_db.value
            for ident_db in so_from_db.identifiers
        )


@pytest.mark.asyncio
async def test_update_source_organization(
        hal_source_institution_pydantic_model: SourceOrganization):
    """
    Test updating an existing SourceOrganization in the graph database.
    :param hal_source_institution_pydantic_model:
    :return:
    """
    dao = _get_source_organization_dao()

    await dao.create(hal_source_institution_pydantic_model)

    so_from_db = await dao.get_by_uid(hal_source_institution_pydantic_model.uid)
    assert so_from_db is not None

    so_from_db.name = "Université Anonyme - Updated"
    # remove one identifier
    so_from_db.identifiers = [
        i for i in so_from_db.identifiers if
        not (i.type == "isni" and i.value == "000000012345678X")
    ]
    # add a new identifier
    so_from_db.identifiers.append(
        SourceOrganizationIdentifier(type="openalex", value="https://openalex.org/I123456789")
    )

    await dao.update(so_from_db)

    so_updated = await dao.get_by_uid(hal_source_institution_pydantic_model.uid)
    assert so_updated is not None
    assert so_updated.name == "Université Anonyme - Updated"
    assert any(i.type == "openalex" and i.value == "https://openalex.org/I123456789"
               for i in so_updated.identifiers)
    assert not any(i.type == "isni" and i.value == "000000012345678X"
                   for i in so_updated.identifiers)


@pytest.mark.asyncio
async def test_source_organization_without_type_defaults_to_organization(
        hal_source_org_without_type_pydantic_model: SourceOrganization
):
    """
    When creating a SourceOrganization without specifying the 'type' field,
    Then it should default to 'ORGANIZATION'.
    """
    # The pydantic model validator already sets the default type.
    assert (hal_source_org_without_type_pydantic_model.type ==
            SourceOrganization.SourceOrganisationType.ORGANIZATION)

    dao = _get_source_organization_dao()

    await dao.create(hal_source_org_without_type_pydantic_model)

    so_from_db = await dao.get_by_uid(hal_source_org_without_type_pydantic_model.uid)
    assert so_from_db is not None
    assert so_from_db.type == SourceOrganization.SourceOrganisationType.ORGANIZATION


@pytest.mark.asyncio
async def test_create_source_organization_cluster_returns_orgs_with_identifiers(
        persisted_cluster_seed_source_org: SourceOrganization,
        persisted_cluster_peer_source_org_1: SourceOrganization,
        persisted_cluster_peer_source_org_2: SourceOrganization,
        persisted_outside_cluster_source_org: SourceOrganization,
):
    """
    Given multiple source organizations persisted in Neo4j
    When we query the cluster from the seed
    Then we get all organizations connected transitively by shared identifiers
    And each returned organization is hydrated with its identifiers (type/value pairs)
    And organizations outside the cluster are not returned.
    """
    dao = _get_source_organization_dao()

    cluster = await dao.create_source_organization_cluster(persisted_cluster_seed_source_org.uid)

    # cluster should include seed + peers (3 orgs total in our fixtures)
    uids = {so.uid for so in cluster}
    assert persisted_cluster_seed_source_org.uid in uids
    assert persisted_cluster_peer_source_org_1.uid in uids
    assert persisted_cluster_peer_source_org_2.uid in uids

    # outside cluster must not be present
    assert persisted_outside_cluster_source_org.uid not in uids

    # each returned org has identifiers hydrated as SourceOrganizationIdentifier objects
    for so in cluster:
        assert isinstance(so, SourceOrganization)
        assert so.identifiers is not None
        assert all(isinstance(i, SourceOrganizationIdentifier) for i in so.identifiers)

    # sanity checks: the shared identifier used to connect the cluster is present
    # (see fixtures below: shared idref=123456789)
    seed = next(s for s in cluster if s.uid == persisted_cluster_seed_source_org.uid)
    assert any(i.type == "idref" and i.value == "123456789" for i in seed.identifiers)

    peer2 = next(s for s in cluster if s.uid == persisted_cluster_peer_source_org_2.uid)
    assert any(
        i.type == "ror" and i.value == "https://ror.org/000000000" for i in peer2.identifiers)


def _get_source_organization_dao() -> SourceOrganizationDAO:
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    return factory.get_dao(SourceOrganization)
