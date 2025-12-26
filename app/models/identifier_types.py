import re
from enum import Enum
from typing import Optional


class AgentIdentifierType(Enum):
    """Base class for agent identifier types"""

    @staticmethod
    def _normalize(s: str) -> str:
        """
        Normalize identifier type:
        - lowercase
        - keep letters only (a–z)
        """
        return re.sub(r"[^a-z]", "", s.lower())

    @classmethod
    def get_identifier_type_from_str(
            cls,
            identifier_type_str: str,
    ) -> Optional["AgentIdentifierType"]:
        """Get the identifier type enum member from a string representation"""
        if not identifier_type_str:
            return None

        normalized_input = cls._normalize(identifier_type_str)

        for identifier_type in cls:
            if cls._normalize(identifier_type.value) == normalized_input:
                return identifier_type

        return None


# Access pattern through a class method in PersonIdentifierType
class PersonIdentifierType(AgentIdentifierType):
    """Person identifier types"""
    ORCID = "orcid"
    IDREF = "idref"
    ID_HAL_S = "id_hal_s"
    ID_HAL_I = "id_hal_i"
    SCOPUS_EID = "scopus_eid"
    LOCAL = "local"
    EPPN = "eppn"

    @classmethod
    def get_pattern(cls, identifier_type):
        """Retrieve the pattern for a given identifier type, if it exists"""
        return PERSON_IDENTIFIER_PATTERNS.get(identifier_type)

    @classmethod
    def validate_identifier(cls, identifier_type, value):
        """Validate an identifier value against its type-specific pattern"""
        pattern = cls.get_pattern(identifier_type)
        if pattern:
            return bool(re.fullmatch(pattern, value))
        # Return True if there's no pattern (e.g., for 'LOCAL')
        return True


PERSON_IDENTIFIER_PATTERNS = {
    PersonIdentifierType.ORCID: "^([0-9]{4}-){3}[0-9]{3}[0-9X]$",
    PersonIdentifierType.IDREF: "^[0-9]{1,9}[A-Z]?$",
    PersonIdentifierType.ID_HAL_S: "^([a-z]+-)*[a-z]+$",
    PersonIdentifierType.ID_HAL_I: "^[0-9]{1,9}$",
    PersonIdentifierType.SCOPUS_EID: "^[0-9]+$",
}


class OrganizationIdentifierType(AgentIdentifierType):
    """Organization identifier types"""
    IDREF = "IdRef"
    ROR = "ror"
    RNSR = "nns"
    LOCAL = "local"
    UAI = "UAI"
    SIREN = "SIREN"
    SIRET = "SIRET"
    WIKIDATA = "Wikidata"
    SCOPUS_ID = "scopus_id"
    HAL = "hal"
    OPEN_ALEX = "openalex"
    ISNI = "isni"
    VIAF = "viaf"


class PublicationIdentifierType(Enum):
    """Publication identifier types"""
    ARXIV = "arxiv"
    DOI = "doi"
    HAL = "hal"
    INERIS = "ineris"
    IRD = "ird"
    NNT = "nnt"
    OPENALEX = "open_alex"
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
    UNKNOWN = "unknown"


class JournalIdentifierType(Enum):
    """Journal identifier types"""
    DOI = "doi"
    ISSN = "issn"
