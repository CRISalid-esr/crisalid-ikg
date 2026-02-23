from typing import Optional, List, ClassVar

from loguru import logger
from pydantic import model_validator, Field

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier, JournalIdentifierFormat
from app.models.sourced_model import SourcedModel


class SourceJournal(SourcedModel):
    """
    Source Journal API model
    """
    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: Optional[str] = None

    source_identifier: str

    publisher: Optional[str] = None

    titles: List[str] = []

    identifiers: List[JournalIdentifier] = Field(default_factory=list)

    issn: Optional[List[str]] = Field(default_factory=list, exclude=True)
    eissn: Optional[List[str]] = Field(default_factory=list, exclude=True)
    issn_l: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _build_identifiers(cls, values):
        identifiers = {}

        for issn_value in values.get("issn", []):
            identifiers[issn_value] = JournalIdentifier(type=JournalIdentifierType.ISSN,
                                                        value=issn_value)

        for eissn_value in values.get("eissn", []):
            identifiers[eissn_value] = JournalIdentifier(type=JournalIdentifierType.ISSN,
                                                         value=eissn_value,
                                                         format=JournalIdentifierFormat.ONLINE)

        if issn_l := values.get("issn_l"):
            identifiers[issn_l] = JournalIdentifier(type=JournalIdentifierType.ISSN,
                                                    value=issn_l)

        values["identifiers"] = list(identifiers.values())
        return values

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        source = values.get("source")
        source_identifier = values.get("source_identifier")
        if not source or not source_identifier:
            logger.warning(f"SourceJournal {values} missing source or source_identifier")
            return values
        values["uid"] = f"{source.lower()}{SourceJournal.IDENTIFIER_SEPARATOR}{source_identifier}"
        return values
