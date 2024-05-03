"""
Person model
"""
from typing import List

from pydantic import validator, root_validator, field_validator

from app.models.agent_identifiers import AgentIdentifier, PersonIdentifier
from app.models.agents import Agent
from app.models.identifier_types import PersonIdentifierType


class Person(Agent[PersonIdentifierType]):
    """
    Person API object
    """

    first_names: List[str] = []
    last_names: List[str] = []

    alternative_names: List[str] = []

    identifiers: List[PersonIdentifier]

    @field_validator("identifiers", mode="after")
    def validate_identifiers(cls, identifiers):
        if identifiers and any(
                ident.type not in PersonIdentifierType for ident in identifiers):
            raise ValueError("All identifiers for a Person must be of type PersonIdentifierType")
        return identifiers
