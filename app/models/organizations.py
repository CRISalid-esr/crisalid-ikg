"""
Person model
"""
from typing import List, Optional

from pydantic import field_validator

from app.models.agent_identifiers import OrganizationIdentifier
from app.models.agents import Agent
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal


class Organization(Agent[OrganizationIdentifierType]):
    """
    Organization API model
    """

    uid: Optional[str] = None  # uid from the database if exists

    names: List[Literal] = []

    identifiers: List[OrganizationIdentifier] = []

    @field_validator('identifiers', mode="after")
    @staticmethod
    def _validate_identifiers(identifiers):
        Organization._prevent_duplicate_identifiers(identifiers)
        return identifiers

    def get_name(self, language: str) -> Literal:
        """
        Get the name in the given language
        :param language: language code
        :return: name
        """
        return next((name for name in self.names if name.language == language), None)
