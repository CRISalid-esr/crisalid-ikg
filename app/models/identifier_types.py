import re
from enum import Enum
from typing import Optional

from loguru import logger


class AgentIdentifierType(Enum):
    """Base class for agent identifier types"""

    @classmethod
    def from_str(
            cls,
            identifier_type_str: str,
    ) -> Optional["AgentIdentifierType"]:
        """Get the identifier type enum member from a string representation"""
        if not identifier_type_str:
            return None
        for identifier_type in cls:
            if identifier_type.value == identifier_type_str:
                return identifier_type
        logger.warning(f"Unknown identifier type: {identifier_type_str}")
        return None


# Access pattern through a class method in PersonIdentifierType
class PersonIdentifierType(AgentIdentifierType):
    """Person identifier types"""
    ORCID = "orcid"
    IDREF = "idref"
    IDHALS = "idhals"
    IDHALI = "idhali"
    SCOPUS = "scopus"
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
    PersonIdentifierType.IDHALS: "^([a-z]+-)*[a-z]+$",
    PersonIdentifierType.IDHALI: "^[0-9]{1,9}$",
    PersonIdentifierType.SCOPUS: "^[0-9]+$",
}


class OrganizationIdentifierType(AgentIdentifierType):
    """Organization identifier types"""
    IDREF = "idref"
    ROR = "ror"
    RNSR = "nns"
    LOCAL = "local"
    UAI = "uai"
    SIREN = "siren"
    SIRET = "siret"
    WIKIDATA = "wikidata"
    SCOPUS_ID = "scopus"
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
