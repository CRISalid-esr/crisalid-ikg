import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.authority_organization_root import AuthorityOrganizationRoot
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.source_organizations import SourceOrganization
from app.services.authority_organizations.authority_organization_service import \
    AuthorityOrganizationService
from app.services.source_contributors.source_organization_service import SourceOrganizationService


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
    assert root.source_organization_uids == []


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
    assert persisted_conflict_peer_source_org_2.uid in root.source_organization_uids

    # ensure provenance tracking exists and contains the conflicting uids
    state_sources = [set(s.source_organization_uids) for s in root.states]
    assert any(persisted_conflict_seed_source_org.uid in ss for ss in state_sources)
    assert any(persisted_conflict_peer_source_org_1.uid in ss for ss in state_sources)


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


@pytest.mark.asyncio
async def test_get_or_create_authority_org_name_only_matches_existing_state_with_identifiers(
        persisted_cluster_seed_source_org: SourceOrganization,
        persisted_cluster_peer_source_org_1: SourceOrganization,  # pylint: disable=unused-argument
        persisted_cluster_peer_source_org_2: SourceOrganization,  # pylint: disable=unused-argument
):
    """
    Given: an AuthorityOrganizationState already exists in graph created from a cluster
           (it has identifiers + a name => normalized_name exists)
    When:  we resolve a cluster containing a single SourceOrganization that has ONLY the name
           (no identifiers)
    Then:  the service must reuse the existing state (same uid), not create a new one.
    """
    auth_service = AuthorityOrganizationService()

    # 1) First call: create the persisted state from identifier-based cluster
    root1 = await auth_service.get_or_create_authority_organization(
        [
            persisted_cluster_seed_source_org,
            persisted_cluster_peer_source_org_1,
            persisted_cluster_peer_source_org_2
        ]
    )
    assert root1 is not None
    assert len(root1.states) == 1
    assert root1.states[0].uid is not None
    existing_state_uid = root1.states[0].uid

    # 2) Second call: name-only source org (no identifiers)
    name_only = SourceOrganization(
        source="manual",
        source_identifier="name-only-1",
        name=persisted_cluster_seed_source_org.name,
        type=persisted_cluster_seed_source_org.type,
        identifiers=[],
    )

    root2 = await auth_service.get_or_create_authority_organization([name_only])

    assert root2 is not None
    assert root2.uid is None, "Name-only cluster alone should not force a root"
    assert len(root2.states) == 1
    assert root2.states[0].uid == existing_state_uid, \
        "Must reuse the existing state by normalized_name"


@pytest.mark.asyncio
async def test_get_or_create_authority_organization_name_only_homonyms_return_root():
    """
    Given: two persisted AuthorityOrganizationStates with the SAME normalized_name,
           each having identifiers (so none is 'state_without_identifiers'),
           and BOTH attached to the SAME root.
    When:  we resolve a cluster containing a single SourceOrganization with only that name
    Then:  service must return the existing root (not pick a random state, not create new).
    """
    dao = _get_authority_org_dao()
    auth_service = AuthorityOrganizationService()

    # 1) Create two states with identical names => identical normalized_name.
    # Use unique identifiers so both can coexist.
    homonym_label = "Homonym Org Nantes 2025 TEST"
    s1 = AuthorityOrganizationState(
        type=SourceOrganization.SourceOrganisationType.INSTITUTION,
        names=[Literal(value=homonym_label, language="fr")],
        identifiers=[
            OrganizationIdentifier(type=OrganizationIdentifierType.ROR,
                                   value="https://ror.org/test-homonym-1"),
            OrganizationIdentifier(type=OrganizationIdentifierType.IDREF, value="TESTIDREF1"),
        ],
    )
    s1.normalize_name()

    s2 = AuthorityOrganizationState(
        type=SourceOrganization.SourceOrganisationType.INSTITUTION,
        names=[Literal(value=homonym_label, language="fr")],
        identifiers=[
            OrganizationIdentifier(type=OrganizationIdentifierType.ROR,
                                   value="https://ror.org/test-homonym-2"),
            OrganizationIdentifier(type=OrganizationIdentifierType.IDREF, value="TESTIDREF2"),
        ],
    )
    s2.normalize_name()

    s1_p = await dao.create_authority_organization_state(s1)
    s2_p = await dao.create_authority_organization_state(s2)

    assert s1_p.uid is not None
    assert s2_p.uid is not None
    assert s1_p.normalized_name == s2_p.normalized_name

    # 2) Create a root and attach both states
    root = AuthorityOrganizationRoot(states=[s1_p, s2_p], source_organization_uids=[])
    root_uid = await dao.create_authority_organization_root(root)
    await dao.attach_authority_organization_states_to_root(
        root_uid=root_uid,
        state_uids=[s1_p.uid, s2_p.uid],
    )

    # 3) Now resolve a name-only source org using service
    name_only = SourceOrganization(
        source="manual",
        source_identifier="name-only-homonym",
        name=homonym_label,
        type=SourceOrganization.SourceOrganisationType.INSTITUTION,
        identifiers=[],
    )

    resolved = await auth_service.get_or_create_authority_organization([name_only])

    assert resolved is not None
    assert resolved.uid == root_uid, \
        "Homonyms with a unique common root => service must return that root"


@pytest.mark.asyncio
async def test_split_cluster_idhal_1_and_idhal_2_must_be_separate_states(
        hal_single_b_pydantic_model: SourceOrganization,
        hal_single_c_pydantic_model: SourceOrganization,
):
    """
    If two orgs share idref/ror but differ on idhal value,
    they must be split into distinct states.
    """
    svc = AuthorityOrganizationService()

    root = svc.split_cluster_into_root_and_states([
        hal_single_b_pydantic_model,
        hal_single_c_pydantic_model,
    ])

    assert len(root.states) >= 2

    state_for_b = next(
        s for s in root.states if hal_single_b_pydantic_model.uid in s.source_organization_uids
    )
    state_for_c = next(
        s for s in root.states if hal_single_c_pydantic_model.uid in s.source_organization_uids
    )

    assert state_for_b is not state_for_c


@pytest.mark.asyncio
async def test_split_cluster_ambiguous_hal_creates_dedicated_state(
        hal_ambiguous_a_pydantic_model: SourceOrganization,
        hal_single_b_pydantic_model: SourceOrganization,
        hal_single_c_pydantic_model: SourceOrganization,
):
    """
    A has two HAL identifiers => excluded_identifiers = {HAL}.
    B has hal=1, C has hal=2.
    => B and C are incompatible with each other.
    => A is incompatible with both B and C.
    => Result: 3 distinct states, no root-only assignment.
    """
    auth_service = AuthorityOrganizationService()

    root = auth_service.split_cluster_into_root_and_states([
        hal_ambiguous_a_pydantic_model,
        hal_single_b_pydantic_model,
        hal_single_c_pydantic_model,
    ])

    # 3 states: A alone, B alone, C alone
    assert len(root.states) == 3

    # A must NOT be root-only anymore
    assert hal_ambiguous_a_pydantic_model.uid not in root.source_organization_uids

    state_for_a = next(
        s for s in root.states
        if hal_ambiguous_a_pydantic_model.uid in s.source_organization_uids
    )

    assert OrganizationIdentifierType.HAL in state_for_a.excluded_identifiers


@pytest.mark.asyncio
async def test_split_cluster_ambiguous_idhal_makes_org_incompatible_with_any_idhal(
        hal_ambiguous_a_pydantic_model: SourceOrganization,
        hal_single_b_pydantic_model: SourceOrganization,
):
    """
    A has two idhal values (ambiguous type 'idhal').
    B has idhal=1.
    Even though they share other identifiers, A must be incompatible with B because
    A is ambiguous on idhal and B carries idhal.
    => should produce at least 2 states (A isolated from B).
    """
    svc = AuthorityOrganizationService()

    root = svc.split_cluster_into_root_and_states([
        hal_ambiguous_a_pydantic_model,
        hal_single_b_pydantic_model,
    ])

    assert len(root.states) >= 2

    # Find which state contains A / B by provenance
    state_for_a = next(s for s in root.states if
                       hal_ambiguous_a_pydantic_model.uid in s.source_organization_uids)
    state_for_b = next(s for s in root.states if
                       hal_single_b_pydantic_model.uid in s.source_organization_uids)

    assert OrganizationIdentifierType.HAL in state_for_a.excluded_identifiers
    assert len(state_for_b.excluded_identifiers) == 0

    assert state_for_a is not state_for_b, \
        "A (ambiguous idhal) must not be grouped with B (has idhal)"


@pytest.mark.asyncio
async def test_ambiguous_hal_is_incompatible_with_any_hal_state(
        hal_ambiguous_a_pydantic_model: SourceOrganization,
        hal_single_b_pydantic_model: SourceOrganization,
):
    """
    A has ambiguous HAL => excluded_identifiers={HAL}.
    B has a HAL.
    => They must NOT be compatible.
    """
    auth_service = AuthorityOrganizationService()

    root = auth_service.split_cluster_into_root_and_states([
        hal_ambiguous_a_pydantic_model,
        hal_single_b_pydantic_model,
    ])

    assert len(root.states) == 2

    state_a = next(
        s for s in root.states
        if hal_ambiguous_a_pydantic_model.uid in s.source_organization_uids
    )
    state_b = next(
        s for s in root.states
        if hal_single_b_pydantic_model.uid in s.source_organization_uids
    )

    assert state_a is not state_b
    assert OrganizationIdentifierType.HAL in state_a.excluded_identifiers


def _get_authority_org_dao():
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    return factory.get_dao(AuthorityOrganizationState)
