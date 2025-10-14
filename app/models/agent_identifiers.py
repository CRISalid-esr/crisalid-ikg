"""
Agent identifiers model
"""
from datetime import datetime
from typing import Generic, Optional

import neo4j
from pydantic import BaseModel, model_validator, field_validator

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
    authenticated: Optional[bool] = None
    authentication_date: Optional[datetime] = None

    @field_validator("authenticated", mode="before")
    @classmethod
    def parse_authenticated(cls, value):
        if isinstance(value, str):
            return value.lower() == "true"
        return value

    @field_validator("authentication_date", mode="before")
    @classmethod
    def convert_neo4j_datetime(cls, value):
        if isinstance(value, neo4j.time.DateTime):
            return value.to_native()  # returns a datetime.datetime object
        return value

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
