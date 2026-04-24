from app.models.group_or_organisation_unit import GroupOrOrganisationUnit
from app.models.agent_identifiers import OrganizationIdentifier


class OrganisationUnit(GroupOrOrganisationUnit):
    """
    Organisation unit global model
    """
    ror: OrganizationIdentifier
