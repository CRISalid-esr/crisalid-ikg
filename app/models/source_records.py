from typing import Optional, List, ClassVar, Dict

from loguru import logger
from pydantic import BaseModel, field_validator, model_validator

from app.models.agents import Agent
from app.models.concepts import Concept
from app.models.document_type import DocumentType, DocumentTypeEnum
from app.models.literal import Literal
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_contributions import SourceContribution
from app.models.source_issue import SourceIssue


class SourceRecord(BaseModel):
    """
    Source Bibliographic Record API model
    (store raw references received from external sources before deduplication)
    """

    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: Optional[str] = None  # uid from the database if exists

    source_identifier: str

    harvester: str

    titles: List[Literal]

    identifiers: List[PublicationIdentifier] = []

    abstracts: List[Literal] = []

    subjects: List[Concept] = []

    document_type: List[DocumentTypeEnum] = []

    contributions: List[SourceContribution] = []

    issue: Optional[SourceIssue] = None

    harvested_for_uids: List[str] = []

    harvested_for: List[Agent] = []


    @field_validator("document_type", mode="before")
    @classmethod
    def document_type_to_enum(cls, value: List[Dict[str, str]]):
        """Convert document type URIs to enum values."""
        return [dt if isinstance(dt, DocumentTypeEnum) else DocumentType(**dt).to_enum() for dt in (
                value) ]

    @field_validator("titles", mode="after")
    @classmethod
    def validate_titles(cls, value):
        """Validate that the titles field is not empty."""
        if not value:
            raise ValueError("Source Record titles cannot be empty")
        return value

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        harvester = values.get("harvester")
        source_identifier = values.get("source_identifier")
        if not harvester or not source_identifier:
            logger.warning(
                f"Source record {values} must have "
                "a source identifier and a harvester to have its uid computed")
            return values
        values["uid"] = f"{harvester.lower()}{cls.IDENTIFIER_SEPARATOR}{source_identifier}"
        return values
