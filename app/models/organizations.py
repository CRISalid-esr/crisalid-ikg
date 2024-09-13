"""
Person model
"""
from typing import List, Optional

from app.models.agent_identifiers import OrganizationIdentifier
from app.models.agents import Agent
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal


class Organization(Agent[OrganizationIdentifierType]):
    """
    Organization API model
    """

    id: Optional[str] = None  # id from the database if exists

    names: List[Literal] = []

    identifiers: List[OrganizationIdentifier]

    def get_name(self, language: str) -> Literal:
        """
        Get the name in the given language
        :param language: language code
        :return: name
        """
        return next((name for name in self.names if name.language == language), None)
