import pytest

from app.models.source_organizations import SourceOrganization
from app.services.authority_organizations.authority_organization_service import \
    AuthorityOrganizationService
from app.services.source_contributors.source_organization_service import SourceOrganizationService


@pytest.mark.current
@pytest.mark.asyncio
async def test_get_or_create_authority_organization_single_state_no_root(
        persisted_cluster_seed_source_org: SourceOrganization,
        persisted_cluster_peer_source_org_1: SourceOrganization,  # pylint: disable=unused-argument
        persisted_cluster_peer_source_org_2: SourceOrganization,  # pylint: disable=unused-argument
):
    """
    Cluster has no contradictions (seed/peers share idref/ror but no type
    ->different value conflicts).
    Service should return a wrapper root with uid=None and exactly one persisted state.
    """
    source_service = SourceOrganizationService()
    auth_service = AuthorityOrganizationService()

    cluster = await source_service.get_cluster(persisted_cluster_seed_source_org.uid)
    root = await auth_service.get_or_create_authority_organization(cluster)

    assert root is not None
    assert root.uid is None, "No contradictions => no root should be created"
    assert len(root.states) == 1
    assert root.states[0].uid is not None, "State must be persisted and have uid"
    assert root.root_only_source_organization_uids == []


@pytest.mark.current
@pytest.mark.asyncio
async def test_get_or_create_authority_organization_conflict_creates_root_and_two_states(
        persisted_conflict_seed_source_org: SourceOrganization,
        persisted_conflict_peer_source_org_1: SourceOrganization,
        persisted_conflict_peer_source_org_2: SourceOrganization,
):
    """
    conflict_a and conflict_b contradict on identifier type 'hal' (different values).
    => service should create at least 2 states and a root (uid != None).
    scanr peer (no hal) is compatible with multiple states => must go to root_only.
    """
    source_service = SourceOrganizationService()
    auth_service = AuthorityOrganizationService()

    cluster = await source_service.get_cluster(persisted_conflict_seed_source_org.uid)
    root = await auth_service.get_or_create_authority_organization(cluster)

    assert root.uid is not None, "Conflicts/root_only => root must be created"
    assert len(root.states) >= 2, "Different hal values => at least two states"

    # scanr peer should be root_only (ambiguous wrt hal state)
    assert persisted_conflict_peer_source_org_2.uid in root.root_only_source_organization_uids

    # ensure provenance tracking exists and contains the conflicting uids
    state_sources = [set(s.source_organization_uids) for s in root.states]
    assert any(persisted_conflict_seed_source_org.uid in ss for ss in state_sources)
    assert any(persisted_conflict_peer_source_org_1.uid in ss for ss in state_sources)


@pytest.mark.current
@pytest.mark.asyncio
async def test_get_or_create_authority_organization_is_idempotent_on_roots(
        persisted_conflict_seed_source_org: SourceOrganization,
        persisted_conflict_peer_source_org_1: SourceOrganization,  # pylint: disable=unused-argument
        persisted_conflict_peer_source_org_2: SourceOrganization,  # pylint: disable=unused-argument
):
    """
    Running get_or_create twice on the same conflict cluster should reuse the same root
    (or at least not create a new one each time).
    """
    source_service = SourceOrganizationService()
    auth_service = AuthorityOrganizationService()

    cluster = await source_service.get_cluster(persisted_conflict_seed_source_org.uid)

    root1 = await auth_service.get_or_create_authority_organization(cluster)
    root2 = await auth_service.get_or_create_authority_organization(cluster)

    assert root1.uid is not None
    assert root2.uid is not None
    assert root1.uid == root2.uid, "Root should be reused for the same set of states"


@pytest.mark.current
@pytest.mark.asyncio
async def test_prepare_source_orgs_drops_ambiguous_identifier_type(
        ambiguous_identifiers_source_org_pydantic_model: SourceOrganization,
):
    """
    _prepare_source_orgs must drop identifier types having multiple values on the same org.
    We validate via split_cluster_into_root_and_states: produced state identifiers
    must NOT contain idref.
    """
    auth_service = AuthorityOrganizationService()

    root = auth_service.split_cluster_into_root_and_states(
        [ambiguous_identifiers_source_org_pydantic_model])
    assert len(root.states) == 1

    state = root.states[0]
    # no idref in state identifiers because it was ambiguous on the source org
    assert all(i.type.value.lower() != "idref" for i in state.identifiers)
