from enum import Enum
from typing import List, ClassVar

from loguru import logger
from pydantic import BaseModel, model_validator

from app.models.source_organization_identifiers import SourceOrganizationIdentifier


class SourceOrganization(BaseModel):
    """
    Source Organization API model
    """

    class SourceOrganisationType(Enum):
        """
        Source Organization types
        """
        INSTITUTION = "institution"
        LABORATORY = "laboratory"
        INSTITUTION_GROUP = "institution_group"
        LABORATORY_GROUP = "laboratory_group"
        RESEARCH_TEAM = "research_team"
        RESEARCH_TEAM_GROUP = "research_team_group"


    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: str
    source: str
    source_identifier: str
    name: str
    type: SourceOrganisationType | None = None
    identifiers: List[SourceOrganizationIdentifier] = []

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        source = values.get("source")
        source_identifier = values.get("source_identifier")
        if not source or not source_identifier:
            logger.warning(f"SourceOrganization {values} missing source or source_identifier")
            return values
        values["uid"] = (f"{source.lower()}"
                         f"{SourceOrganization.IDENTIFIER_SEPARATOR}"
                         f"{source_identifier}")
        return values
