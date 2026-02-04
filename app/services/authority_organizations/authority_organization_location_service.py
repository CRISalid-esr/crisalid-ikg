from __future__ import annotations

class AuthorityOrganizationLocationService:
    """
    Handle location information for AuthorityOrganizations
    """

    async def add_location_from_source_organizations(self, _, state_uid: str):
        """
        Compute location information for an updated AuthorityOrganizationState
        :param _: unused (for compatibility with signal handlers)
        :param state_uid: the AuthorityOrganizationState uid
        :return:
        """
