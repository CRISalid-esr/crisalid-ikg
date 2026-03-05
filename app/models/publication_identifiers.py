"""
Agent identifiers model
"""
from loguru import logger

from pydantic import BaseModel, field_validator

from app.models.identifier_types import PublicationIdentifierType


class PublicationIdentifier(BaseModel):
    """Agent identifier model"""

    type: PublicationIdentifierType
    value: str

    def dict(self, **kwargs):
        return super().dict(**kwargs) | {"type": self.type.value}

    @field_validator('type', mode="before")
    @classmethod
    def _allow_unknown_identifier_type(cls, value):
        if value not in [member.value for member in PublicationIdentifierType]:
            logger.warning("Unknown publication identifier type submitted: %s", value)
            return PublicationIdentifierType.UNKNOWN.value
        return value
