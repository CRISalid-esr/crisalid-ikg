from enum import Enum


class AgentIdentifierType(Enum):
    """Base class for agent identifier types"""
    pass



class PersonIdentifierType(AgentIdentifierType):
    """Person identifier types"""
    ORCID = "orcid"
    IDREF = "idref"
    ID_HAL_S = "idhal_s"
    SCOPUS_EID = "scopus_eid"
    LOCAL = "local"


class OrganizationIdentifierType(AgentIdentifierType):
    """Organization identifier types"""
    IDREF = "IdRef"
    ROR = "ROR"
