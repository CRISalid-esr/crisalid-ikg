"""
Agent identifiers model
"""
from typing import Generic

from pydantic import BaseModel, model_validator

from app.models.identifier_types import PersonIdentifierType, OrganizationIdentifierType
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

    @model_validator(mode="before")
    @classmethod
    def _uppercase_uai(cls, values):
        """"""
        if values.get("type") == OrganizationIdentifierType.UAI:
            values["value"] = values["value"].upper()
        return values
