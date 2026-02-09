import re
from enum import Enum
from typing import Optional

from loguru import logger


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
    def from_str(
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
        logger.warning(f"Unknown identifier type: {identifier_type_str}")
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
    # --PUBLICATION IDENTIFIERS--
    ARXIV = "arxiv"
    BIBCODE = "bibcode"
    BIORXIV = "biorxiv"
    CERN = "cern"
    CHEMRXIV = "chemrxiv"
    DOI = "doi"
    ENSAM = "ensam"
    HAL = "hal"
    INERIS = "ineris"
    INSPIRE = "inspire"
    IRD = "ird"
    IRSTEA = "irstea"
    IRTHESAURUS = "irthesaurus"
    MEDITAGRI = "meditagri"
    NNT = "nnt"
    OKINA = "okina"
    OATAO = "oatao"
    OPENALEX = "openalex"
    PII = "pii"
    PMID = "pmid"
    PPN = "ppn"
    PRODINRA = "prodinra"
    PUBMEDCENTRAL = "pubmedcentral"
    SCIENCESPO = "sciencespo"
    SWHID = "swhid"
    URI = "uri"
    UNKNOWN = "unknown"
    WOS = "wos"



class JournalIdentifierType(Enum):
    """Journal identifier types"""
    DOI = "doi"
    ISSN = "issn"
