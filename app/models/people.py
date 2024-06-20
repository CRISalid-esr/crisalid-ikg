"""
Person model
"""
from typing import List, Optional

from pydantic import field_validator

from app.models.agent_identifiers import PersonIdentifier
from app.models.agents import Agent
from app.models.identifier_types import PersonIdentifierType
from app.models.people_names import PersonName


class Person(Agent[PersonIdentifierType]):
    """
    Person API object
    """

    id:Optional[str] = None # id from the database if exists

    names: List[PersonName] = []

    identifiers: List[PersonIdentifier]

    @field_validator("identifiers", mode="after")
    def validate_identifiers(cls, identifiers):
        if identifiers and any(
                ident.type not in PersonIdentifierType for ident in identifiers):
            raise ValueError("All identifiers for a Person must be of type PersonIdentifierType")
        return identifiers

    def get_identifier(self, identifier_type: PersonIdentifierType) -> PersonIdentifier:
        """
        Get the identifier of the given type
        :param identifier_type: identifier type
        :return: identifier
        """
        return next((ident for ident in self.identifiers if ident.type == identifier_type), None)
