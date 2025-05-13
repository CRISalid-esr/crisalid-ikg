from typing import Optional, List, ClassVar

from loguru import logger
from pydantic import BaseModel, model_validator, Field

from app.models.identifier_types import JournalIdentifierType
from app.models.journal_identifiers import JournalIdentifier, JournalIdentifierFormat
from app.services.journals.issn_info import IssnInfo


class Journal(BaseModel):
    """
    Journal API model
    """
    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: Optional[str] = None

    publisher: Optional[str] = None

    titles: List[str] = []

    identifiers: List[JournalIdentifier] = Field(default_factory=list)

    issn_l: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        issn_l = values.get("issn_l")
        if not issn_l:
            logger.warning(f"Journal {values} missing issn_l")
            return values
        values["uid"] = f"issn-l{cls.IDENTIFIER_SEPARATOR}{issn_l}"
        return values

    @classmethod
    def from_issn_info(cls, issn_info: IssnInfo) -> "Journal":
        """
        Create a Journal object from information returned by the ISSN portal
        :param issn_info: IssnInfo object
        :return: Journal object
        """
        identifiers = []
        for issn, fmt in issn_info.related_issns_with_format.items():
            try:
                format_enum = JournalIdentifierFormat(fmt) if fmt else None
            except ValueError:
                logger.warning(f"Unknown format {fmt} for ISSN {issn}")
                format_enum = None  # Unknown format

            identifiers.append(JournalIdentifier(
                type=JournalIdentifierType.ISSN,
                value=issn,
                format=format_enum
            ))

        return cls(
            issn_l=issn_info.issn_l,
            titles=[issn_info.title] if issn_info.title else [],
            identifiers=identifiers,
            publisher=issn_info.publisher,
        )
