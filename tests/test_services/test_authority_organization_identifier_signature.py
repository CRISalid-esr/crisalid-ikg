from __future__ import annotations

import asyncio

import pytest

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.authority_organization_dao import AuthorityOrganizationDAO
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.authority_organization_state import AuthorityOrganizationState
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.source_organizations import SourceOrganization


def _get_authority_org_dao():
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    return factory.get_dao(AuthorityOrganizationState)


def _state_with_identifiers(
        items: list[tuple[OrganizationIdentifierType, str]]) -> AuthorityOrganizationState:
    s = AuthorityOrganizationState(
        type=SourceOrganization.SourceOrganisationType.INSTITUTION,
        names=[Literal(value="Signature Test Org", language="fr")],
        identifiers=[OrganizationIdentifier(type=t, value=v) for t, v in items],
    )
    s.normalize_name()
    return s


@pytest.mark.asyncio
async def test_create_state_is_idempotent_by_identifier_signature_order_independent():
    """
    GIVEN two authority organization states with the same identifiers in different orders
    WHEN both are created
    THEN both must resolve to the same authority organization state node
    :return:
    """
    dao: AuthorityOrganizationDAO = _get_authority_org_dao()

    s1 = _state_with_identifiers([
        (OrganizationIdentifierType.HAL, "111023"),
        (OrganizationIdentifierType.ROR, "03nh7d505"),
        (OrganizationIdentifierType.IDREF, "03063525X"),
        (OrganizationIdentifierType.ISNI, "0000000122039289"),
    ])

    s2 = _state_with_identifiers([
        (OrganizationIdentifierType.ISNI, "0000000122039289"),
        (OrganizationIdentifierType.IDREF, "03063525X"),
        (OrganizationIdentifierType.ROR, "03nh7d505"),
        (OrganizationIdentifierType.HAL, "111023"),
    ])

    created_1 = await dao.create_authority_organization_state(s1)
    created_2 = await dao.create_authority_organization_state(s2)

    assert created_1.uid is not None
    assert created_2.uid is not None
    assert created_1.uid == created_2.uid, \
        "MERGE on identifier_signature should reuse the same state"


@pytest.mark.asyncio
async def test_create_state_concurrent_calls_do_not_duplicate_by_signature():
    """
    GIVEN two concurrent create calls with the same identifier set
    WHEN both are executed
    THEN both must resolve to the same authority organization state node
    :return:
    """
    dao: AuthorityOrganizationDAO = _get_authority_org_dao()

    base_items = [
        (OrganizationIdentifierType.HAL, "1086798"),
        (OrganizationIdentifierType.ROR, "03nh7d505"),
        (OrganizationIdentifierType.IDREF, "03063525X"),
        (OrganizationIdentifierType.ISNI, "0000000122039289"),
    ]

    async def _create_one():
        s = _state_with_identifiers(base_items)
        return await dao.create_authority_organization_state(s)

    # simulate concurrency
    created_a, created_b = await asyncio.gather(_create_one(), _create_one())

    assert created_a.uid is not None
    assert created_b.uid is not None
    assert created_a.uid == created_b.uid, "Both concurrent creates must resolve to the same node"


@pytest.mark.asyncio
async def test_update_state_recomputes_identifier_signature_stably():
    """
    GIVEN an authority organization state created with a subset of identifiers
    WHEN another identifier is added and the state is updated
    THEN the updated state must have the same uid when created again with the full identifier set
    :return:
    """
    dao: AuthorityOrganizationDAO = _get_authority_org_dao()

    s = _state_with_identifiers([
        (OrganizationIdentifierType.IDREF, "03063525X"),
        (OrganizationIdentifierType.ROR, "03nh7d505"),
    ])
    created = await dao.create_authority_organization_state(s)
    assert created.uid is not None

    # Add another identifier and update
    created.identifiers.append(
        OrganizationIdentifier(type=OrganizationIdentifierType.ISNI, value="0000000122039289")
    )
    created.normalize_name()
    updated = await dao.update_authority_organization_state(created)

    assert updated.uid == created.uid

    # create another state with the full identifier set => must resolve to same uid
    s2 = _state_with_identifiers([
        (OrganizationIdentifierType.ROR, "03nh7d505"),
        (OrganizationIdentifierType.IDREF, "03063525X"),
        (OrganizationIdentifierType.ISNI, "0000000122039289"),
    ])
    created_2 = await dao.create_authority_organization_state(s2)
    assert created_2.uid == created.uid, \
        "After update, signature should match the expanded identifier set"
