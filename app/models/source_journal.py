from typing import Optional, List, ClassVar

from pydantic import BaseModel, model_validator, Field

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier


class SourceJournal(BaseModel):
    """
    Source Review Issue API model
    """
    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: Optional[str] = None

    source_identifier: str

    source: str

    publisher: Optional[str] = None

    titles: List[str] = []

    identifiers: List[JournalIdentifier] = Field(default_factory=list)

    issn: Optional[List[str]] = Field(default_factory=list, exclude=True)
    eissn: Optional[List[str]] = Field(default_factory=list, exclude=True)
    issn_l: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _build_identifiers(cls, values):
        identifiers = {
            "issn": {},
            "eissn": {},
        }

        for issn_value in values.get("issn", []):
            identifiers["issn"][issn_value] = JournalIdentifier(type=JournalIdentifierType.ISSN,
                                                                value=issn_value)

        for eissn_value in values.get("eissn", []):
            identifiers["eissn"][eissn_value] = JournalIdentifier(type=JournalIdentifierType.EISSN,
                                                                  value=eissn_value)

        if issn_l := values.get("issn_l"):
            identifiers["issn"][issn_l] = JournalIdentifier(type=JournalIdentifierType.ISSN,
                                                            value=issn_l)

        values["identifiers"] = list(identifiers["issn"].values()) + list(
            identifiers["eissn"].values())
        return values

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        source = values.get("source")
        source_identifier = values.get("source_identifier")
        if not source or not source_identifier:
            return values
        values["uid"] = f"{source.lower()}{SourceJournal.IDENTIFIER_SEPARATOR}{source_identifier}"
        return values
