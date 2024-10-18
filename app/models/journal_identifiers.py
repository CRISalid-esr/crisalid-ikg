"""
Agent identifiers model
"""

from pydantic import BaseModel

from app.models.identifier_types import JournalIdentifierType


class JournalIdentifier(BaseModel):
    """Journal identifier model"""

    type: JournalIdentifierType
    value: str

    def dict(self, **kwargs):
        return super().dict(**kwargs) | {"type": self.type.value}
