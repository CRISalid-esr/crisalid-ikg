from enum import Enum


class GenericOrganizationType(str, Enum):
    INSTITUTION = "institution"
    INSTITUTION_SUBDIVISION = "institution_subdivision"
    UNIT = "unit"
    UNIT_SUBDIVISION = "unit_subdivision"
    TEAM = "team"


class NationalOrganizationType(str, Enum):
    UNIV = "UNIV"
    EPE = "EPE"
    COMUE = "COMUE"
    UMR = "UMR"
    UAR = "UAR"
    UR = "UR"
    IRL = "IRL"
    UFR = "UFR"
    FAC = "FAC"
    TEAM = "TEAM"
    THEME = "THEME"


class MissionType(str, Enum):
    RESEARCH = "research"
    SCIENTIFIC_SERVICES = "scientific_services"
    ADMINISTRATIVE_SERVICES = "administrative_services"


class OrgMembershipPosition(str, Enum):
    MAIN_SUPERVISION = "main_supervision"
    ASSOCIATED_SUPERVISION = "associated_supervision"
    PARTICIPATING_SUPERVISION = "participating_supervision"


ALLOWED_NATIONAL_TYPES_BY_GENERIC_TYPE: dict = {
    GenericOrganizationType.INSTITUTION: {
        NationalOrganizationType.EPE,
        NationalOrganizationType.UNIV,
        NationalOrganizationType.COMUE,
    },
    GenericOrganizationType.UNIT: {
        NationalOrganizationType.UMR,
        NationalOrganizationType.UAR,
        NationalOrganizationType.UR,
        NationalOrganizationType.IRL,
    },
    GenericOrganizationType.INSTITUTION_SUBDIVISION: {
        NationalOrganizationType.UFR,
        NationalOrganizationType.FAC,
    },
    GenericOrganizationType.UNIT_SUBDIVISION: set(),
    GenericOrganizationType.TEAM: {
        NationalOrganizationType.TEAM,
        NationalOrganizationType.THEME,
    },
}
