"""
Agent identifiers model
"""

from pydantic import BaseModel

from app.models.identifier_types import PublicationIdentifierType


class PublicationIdentifier(BaseModel):
    """Agent identifier model"""

    type: PublicationIdentifierType
    value: str

    def dict(self, **kwargs):
        return super().dict(**kwargs) | {"type": self.type.value}
