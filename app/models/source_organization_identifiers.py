from typing import Dict, Any, Optional, List

from loguru import logger
from pydantic import BaseModel, model_validator


class RorGeoNamesLocation(BaseModel):
    """
    ROR GeoNames Location API model
    """
    continent_code: str
    continent_name: str
    country_code: str
    country_name: str
    country_subdivision_code: Optional[str]
    country_subdivision_name: Optional[str]
    geonames_id: int
    lat: float
    lng: float
    name: str


class RORExtraInformation(BaseModel):
    """
    ROR Extra Information API model
    """
    established: Optional[int]
    status: str
    types: List[str]
    geonames_locations: List[RorGeoNamesLocation]


class SourceOrganizationIdentifier(BaseModel):
    """
    Source Organization Identifier API model
    """

    type: str
    value: str

    extra_information: Dict[str, Any] = {}  # New field for additional data

    @model_validator(mode="after")
    def _handle_extra_information(self):
        if self.type == "ror":
            ror = RORExtraInformation.model_validate(self.extra_information)
            self.extra_information = ror.model_dump()
        else:
            # Explicitly drop any extra_information for non-ROR types
            logger.warning(f"Extra information for {self.type} identifier dropped.")
            self.extra_information = {}

        return self
