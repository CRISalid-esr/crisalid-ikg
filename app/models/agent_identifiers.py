"""
Agent identifiers model
"""
from typing import Generic

from pydantic import BaseModel

from app.models.identifier_types import AgentIdentifierType, PersonIdentifierType, OrganizationIdentifierType
from app.models.shared_types import IdType


class AgentIdentifier(BaseModel, Generic[IdType]):
    """Agent identifier model"""

    type: IdType
    value: str

    def dict(self, **kwargs):
        return super().dict(**kwargs) | {"type": self.type.value}


class PersonIdentifier(AgentIdentifier[PersonIdentifierType]):
    """Person identifier model"""
    type: PersonIdentifierType


class OrganizationIdentifier(AgentIdentifier[OrganizationIdentifierType]):
    """Organization identifier model"""
    type: OrganizationIdentifierType
