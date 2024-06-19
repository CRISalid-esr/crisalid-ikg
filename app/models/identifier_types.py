from enum import Enum


class AgentIdentifierType(Enum):
    """Base class for agent identifier types"""
    pass



class PersonIdentifierType(AgentIdentifierType):
    """Person identifier types"""
    ORCID = "ORCID"
    IDREF = "IdRef"
    ID_HAL_S = "IdHalS"
    SCOPUS_EID = "ScopusEID"
    LOCAL = "local"


class OrganizationIdentifierType(AgentIdentifierType):
    """Organization identifier types"""
    IDREF = "IdRef"
    ROR = "ROR"
