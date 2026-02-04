import json
from typing import Dict, Any, Optional, List

from loguru import logger
from pydantic import BaseModel, model_validator, field_serializer, field_validator


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
            if self.extra_information == {}:
                logger.warning(f"Extra information for {self.type} identifier is empty.")
            else:
                ror = RORExtraInformation.model_validate(self.extra_information)
                self.extra_information = ror.model_dump()
        else:
            # Explicitly drop any extra_information for non-ROR types
            logger.warning(f"Extra information for {self.type} identifier dropped.")
            self.extra_information = {}

        return self

    @field_serializer('extra_information')
    def serialize_extra_information(self, value: Dict[str, Any]):
        """
        Allow the storage of extra information as string inside the nodes
        """
        return json.dumps(value)

    @field_validator("extra_information", mode="before")
    @classmethod
    def parse_payload(cls, v):
        """
        Ensure that the extra information can be read from string at hydration time
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError("payload must be valid JSON") from e
        return v
