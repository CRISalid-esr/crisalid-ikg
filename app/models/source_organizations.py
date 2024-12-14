from typing import List

from pydantic import BaseModel

from app.models.source_organization_identifiers import SourceOrganizationIdentifier


class SourceOrganization(BaseModel):
    """
    Source Organization API model
    """

    source: str
    source_identifier: str
    name: str
    type: str | None = None
    identifiers: List[SourceOrganizationIdentifier] = []
