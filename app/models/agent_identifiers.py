"""
Agent identifiers model
"""
from typing import Generic

from pydantic import BaseModel

from app.models.identifier_types import AgentIdentifierType, PersonIdentifierType, OrganizationIdentifierType
from app.models.shared_types import IdType


class AgentIdentifier(Generic[IdType], BaseModel):
    """Agent identifier model"""

    type: IdType
    value: str


class PersonIdentifier(AgentIdentifier[PersonIdentifierType]):
    """Person identifier model"""


class OrganizationIdentifier(AgentIdentifier[OrganizationIdentifierType]):
    """Organization identifier model"""
