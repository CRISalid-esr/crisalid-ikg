from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, model_validator

from app.models.literal import Literal


class GenericOrganisationType(Enum):
    """Generic organisation types"""
    INSTITUTION = "institution"
    INSTITUTION_SUBDIVISION = "institution_subdivision"
    UNIT = "unit"
    UNIT_SUBDIVISION = "unit_subdivision"
    TEAM = "team"

class NationalOrganisationType(Enum):
    """RNeST organisation types"""
    UMR = "UMR"
    EPE = "EPE"

class MissionType(Enum):
    """Institution mission types"""
    RESEARCH = "research"
    SCIENTIFIC_SERVICES = "scientific_services"
    ADMINISTRATIVE_SERVICES = "administrative_services"

class GroupOrOrganisationUnit(BaseModel):
    """
    Group or organisation unit global model
    """
    generic_type: GenericOrganisationType
    national_type: Optional[NationalOrganisationType]
    local_type: Optional[str]

    main_mission: Optional[MissionType]
    secondary_mission: Optional[list[MissionType]]

    short_labels: List[Literal]
    long_labels: List[Literal]
    descriptions: Optional[List[Literal]]

    @model_validator(mode="after")
    def check_national_type_or_local_type(self):
        """
        Ensure that at least one of the two types (national or local) is present
        """
        if self.national_type is None and self.local_type is None:
            short_labels = self.short_labels
            label = short_labels[0] if short_labels else "unknown"
            raise ValueError(
                f"At least one of 'type' or 'local_type' must be provided for organisation {label}"
            )

        return self
