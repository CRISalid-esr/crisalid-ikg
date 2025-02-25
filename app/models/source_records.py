import re
from datetime import datetime
from typing import Optional, List, ClassVar, Dict

import isodate
from loguru import logger
from pydantic import BaseModel, field_validator, model_validator, HttpUrl

from app.models.agents import Agent
from app.models.concepts import Concept
from app.models.document_type import DocumentType, DocumentTypeEnum
from app.models.literal import Literal
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_contributions import SourceContribution
from app.models.source_issue import SourceIssue
from app.services.source_records.source_record_url_service import SourceRecordUrlService
from app.utils.date.partial_iso_8601 import parse_partial_iso8601


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

    issued: Optional[datetime] = None

    raw_issued: Optional[str] = None

    url: Optional[HttpUrl] = None

    @field_validator("document_type", mode="before")
    @classmethod
    def document_type_to_enum(cls, value: List[Dict[str, str]]):
        """Convert document type URIs to enum values."""
        return [dt if isinstance(dt, DocumentTypeEnum) else DocumentType(**dt).to_enum() for dt in (
            value)]

    @field_validator("titles", mode="after")
    @classmethod
    def validate_titles(cls, value):
        """Validate that the titles field is not empty."""
        if not value:
            raise ValueError("Source Record titles cannot be empty")
        return value

    @field_validator("issued", mode="before")
    @classmethod
    def _validate_issued(cls, value):
        try:
            if isinstance(value, str):
                # if format is 2022-07-18 00:00:00, convert to 2022-07-18T00:00:00
                value = re.sub(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})", r"\1T\2", value)
                return isodate.parse_datetime(value)
            if isinstance(value, datetime):
                return value
            return None
        except (isodate.ISO8601Error, ValueError):
            logger.error(f"Invalid ISO 8601 datetime format: {value}")
            return None

    @field_validator("raw_issued", mode="before")
    @classmethod
    def _validate_raw_issued(cls, value):
        return parse_partial_iso8601(value)

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

    @model_validator(mode="before")
    @classmethod
    def _compute_source_record_url(cls, values):
        try:
            values["url"] = SourceRecordUrlService.compute_url(values["harvester"],
                                                               values["source_identifier"])
            return values
        except (ValueError, KeyError):
            logger.error(f"Failed to compute source record URL for {values}")
            return values
