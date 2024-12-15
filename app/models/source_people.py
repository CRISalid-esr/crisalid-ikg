from typing import List, ClassVar

from loguru import logger
from pydantic import BaseModel, model_validator

from app.models.source_person_identifiers import SourcePersonIdentifier


class SourcePerson(BaseModel):
    """
    Source Contributor model
    """

    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: str
    source: str
    source_identifier: str
    name: str

    identifiers: List[SourcePersonIdentifier] = []

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        if values.get("uid"):
            return values
        source = values.get("source")
        source_identifier = values.get("source_identifier")
        if not source or not source_identifier:
            logger.warning(
                f"Source person {values} must have "
                "a source identifier and a source to have its uid computed")
            return values
        values["uid"] = f"{source.lower()}{cls.IDENTIFIER_SEPARATOR}{source_identifier}"
        return values
