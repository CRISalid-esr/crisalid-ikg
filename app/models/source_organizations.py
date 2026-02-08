from enum import Enum
from typing import List, ClassVar, Set

from loguru import logger
from pydantic import model_validator, field_validator

from app.models.source_organization_identifiers import SourceOrganizationIdentifier
from app.models.sourced_model import SourcedModel


class SourceOrganization(SourcedModel):
    """
    Source Organization API model
    """

    class SourceOrganisationType(Enum):
        """
        Source Organization types
        """
        ORGANIZATION = "organization"  # generic placeholder when type is not specified
        INSTITUTION = "institution"
        LABORATORY = "laboratory"
        INSTITUTION_GROUP = "institution_group"
        LABORATORY_GROUP = "laboratory_group"
        RESEARCH_TEAM = "research_team"
        RESEARCH_TEAM_GROUP = "research_team_group"

    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: str
    source_identifier: str
    name: str
    type: SourceOrganisationType = SourceOrganisationType.ORGANIZATION
    identifiers: List[SourceOrganizationIdentifier] = []

    @field_validator("type", mode="before")
    @classmethod
    def _set_default_type(cls, v):
        if v is None:
            return SourceOrganization.SourceOrganisationType.ORGANIZATION
        return v

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        source = values.get("source")
        source_identifier = values.get("source_identifier")
        if not source or not source_identifier:
            logger.warning(f"SourceOrganization {values} missing source or source_identifier")
            return values
        values["uid"] = (f"{source}"
                         f"{SourceOrganization.IDENTIFIER_SEPARATOR}"
                         f"{source_identifier}")
        return values

    def get_ambiguous_identifiers(self) -> Set[str]:
        """
        Return identifier types that appear more than once on this source organization.

        Example:
        - idhal x2 → {"idhal"}
        - idref x1, viaf x2 → {"viaf"}
        """
        seen: set[str] = set()
        ambiguous: set[str] = set()
        for ident in self.identifiers or []:
            if not ident.type:
                continue
            t = ident.type.lower()
            if t in seen:
                ambiguous.add(t)
            else:
                seen.add(t)
        return ambiguous
