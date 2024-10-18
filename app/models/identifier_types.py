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
    ARXIV = "arxiv"
    DOI = "doi"
    HAL = "hal"
    INERIS = "ineris"
    IRD = "ird"
    NNT = "nnt"
    OPENALEX = "openalex"
    PII = "pii"
    PMID = "pmid"
    PMC = "pmcid"
    PUBMED = "pubmed"
    PUBMEDCENTRAL = "pubmedcentral"
    PPN = "ppn"
    PRODINRA = "prodinra"
    SCIENCESPO = "sciencespo"
    URI = "uri"
    WOS = "wos"


class JournalIdentifierType(Enum):
    """Journal identifier types"""
    DOI = "doi"
    ISSN = "issn"
    EISSN = "eissn"
