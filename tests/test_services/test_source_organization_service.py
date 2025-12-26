import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.source_organizations import SourceOrganization
from app.services.source_contributors.source_organization_service import SourceOrganizationService


def _get_source_org_dao() -> SourceOrganizationDAO:
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    return factory.get_dao(SourceOrganization)


@pytest.mark.asyncio
async def test_service_create_or_update_creates_when_missing(
        hal_source_institution_pydantic_model: SourceOrganization,
):
    """
    Service should create a new source organization when it does not exist.
    :param hal_source_institution_pydantic_model:
    :return:
    """
    service = SourceOrganizationService()

    created = await service.create_or_update_source_organization(
        hal_source_institution_pydantic_model)
    assert created.uid == hal_source_institution_pydantic_model.uid

    # verify persisted
    dao = _get_source_org_dao()
    from_db = await dao.get_by_uid(hal_source_institution_pydantic_model.uid)
    assert from_db is not None
    assert from_db.name == hal_source_institution_pydantic_model.name
    assert any(i.type == "idref" and i.value == "123456789" for i in from_db.identifiers)


@pytest.mark.asyncio
async def test_service_create_or_update_updates_when_exists(
        hal_source_institution_pydantic_model: SourceOrganization,
):
    """
    Service should update an existing source organization.
    :param hal_source_institution_pydantic_model:
    :return:
    """
    dao = _get_source_org_dao()
    await dao.create(hal_source_institution_pydantic_model)

    # change some data
    hal_source_institution_pydantic_model.name = "Université Anonyme (updated)"

    service = SourceOrganizationService()
    updated = await service.create_or_update_source_organization(
        hal_source_institution_pydantic_model)
    assert updated.name == "Université Anonyme (updated)"

    from_db = await dao.get_by_uid(hal_source_institution_pydantic_model.uid)
    assert from_db.name == "Université Anonyme (updated)"


@pytest.mark.asyncio
async def test_service_get_cluster_returns_transitive_cluster(
        persisted_cluster_seed_source_org: SourceOrganization,
        persisted_cluster_peer_source_org_1: SourceOrganization,
        persisted_cluster_peer_source_org_2: SourceOrganization,
        persisted_outside_cluster_source_org: SourceOrganization,
):
    """
    Service should delegate to DAO cluster query and return the transitive cluster.
    """
    service = SourceOrganizationService()
    cluster = await service.get_cluster(persisted_cluster_seed_source_org.uid)

    uids = {so.uid for so in cluster}
    assert persisted_cluster_seed_source_org.uid in uids
    assert persisted_cluster_peer_source_org_1.uid in uids
    assert persisted_cluster_peer_source_org_2.uid in uids
    assert persisted_outside_cluster_source_org.uid not in uids
