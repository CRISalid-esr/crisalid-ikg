from __future__ import annotations

from typing import List

from app.models.authority_organization import AuthorityOrganization
from app.models.authority_organization_state import AuthorityOrganizationState


class AuthorityOrganizationRoot(AuthorityOrganization):
    """
    Groups multiple states related of an evolving/splitting/merging organization.
    """
    states: List[AuthorityOrganizationState] = []

    root_only_source_organization_uids: List[str] = []
