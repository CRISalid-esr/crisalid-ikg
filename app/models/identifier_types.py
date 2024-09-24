from enum import Enum


class AgentIdentifierType(Enum):
    """Base class for agent identifier types"""


class PersonIdentifierType(AgentIdentifierType):
    """Person identifier types"""
    ORCID = "orcid"
    IDREF = "idref"
    ID_HAL_S = "id_hal_s"
    ID_HAL_I = "id_hal_i"
    SCOPUS_EID = "scopus_eid"
    LOCAL = "local"


class OrganizationIdentifierType(AgentIdentifierType):
    """Organization identifier types"""
    IDREF = "IdRef"
    ROR = "ROR"
    RNSR = "RNSR"
    LOCAL = "local"

class PublicationIdentifierType(Enum):
    """Publication identifier types"""
    DOI = "doi"
    URI = "uri"
    PMID = "pmid"
    OPENALEX = "openalex"
    ARXIV = "arxiv"
    HAL = "hal"
    NNT = "nnt"
