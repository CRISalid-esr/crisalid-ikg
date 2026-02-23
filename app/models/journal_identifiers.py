"""
Agent identifiers model
"""
from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, model_validator

from app.models.identifier_types import JournalIdentifierType


class JournalIdentifierFormat(Enum):
    """Journal identifier format enum"""
    PRINT = "Print"
    ONLINE = "Online"


class JournalIdentifier(BaseModel):
    """Journal identifier model"""

    IDENTIFIER_SEPARATOR: ClassVar[str] = "-"

    uid: Optional[str] = None

    type: JournalIdentifierType
    format: Optional[JournalIdentifierFormat] = None
    value: str

    last_checked: Optional[int] = None

    def dict(self, **kwargs):
        return super().model_dump(**kwargs) | {"type": self.type.value} | {
            "format": self.format.value if self.format else None}

    @model_validator(mode="before")
    @classmethod
    def _build_uid(cls, values):
        type_ = values.get("type")
        value = values.get("value")
        if not type_ or not value:
            return values
        # if type is a JournalIdentifierType, get its value
        if isinstance(type_, JournalIdentifierType):
            type_ = type_.value
        values["uid"] = f"{str(type_).lower()}{JournalIdentifier.IDENTIFIER_SEPARATOR}{value}"
        return values
