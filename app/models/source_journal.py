from typing import Optional, List

from pydantic import BaseModel, model_validator, Field

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier


class SourceJournal(BaseModel):
    """
    Source Review Issue API model
    """

    uid: Optional[str] = None

    source_identifier: str

    source: str

    publisher: Optional[str] = None

    titles: List[str] = []

    identifiers: List[JournalIdentifier] = Field(default_factory=list)

    @model_validator(mode="before")
    def _build_identifiers(self, values):
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
