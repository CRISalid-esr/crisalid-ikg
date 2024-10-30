from typing import Optional, List

from pydantic import BaseModel, field_validator

from app.models.agents import Agent
from app.models.concepts import Concept
from app.models.document_type import DocumentType
from app.models.literal import Literal
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_contributions import SourceContribution
from app.models.source_issue import SourceIssue


class SourceRecord(BaseModel):
    """
    Source Bibliographic Record API model
    (store raw references received from external sources before deduplication)
    """

    uid: Optional[str] = None  # uid from the database if exists

    source_identifier: str

    harvester: str

    titles: List[Literal]

    identifiers: List[PublicationIdentifier] = []

    abstracts: List[Literal] = []

    subjects: List[Concept] = []

    document_type: List[DocumentType] = []

    contributions: List[SourceContribution] = []

    issue: Optional[SourceIssue] = None

    harvested_for: List[Agent] = []

    @field_validator("titles", mode="after")
    @classmethod
    def validate_titles(cls, value):
        """Validate that the titles field is not empty."""
        if not value:
            raise ValueError("Source Record titles cannot be empty")
        return value
