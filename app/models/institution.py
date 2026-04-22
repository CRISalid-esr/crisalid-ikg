"""
Institution model
"""
from app.models.agent_identifiers import OrganizationIdentifier
from app.models.organisation_unit import OrganisationUnit


class Institution(OrganisationUnit):
    """
    Institution model
    """
    internal: bool
    uai: OrganizationIdentifier
    siren: OrganizationIdentifier
