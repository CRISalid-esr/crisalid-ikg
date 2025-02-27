"""
Organization model
"""
from typing import List, Optional

from pydantic import field_validator

from app.models.agent_identifiers import OrganizationIdentifier
from app.models.agents import Agent
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.places import Place
from app.models.structured_physical_address import StructuredPhysicalAddress


class Organization(Agent[OrganizationIdentifierType]):
    """
    Organization API model
    """

    uid: Optional[str] = None  # UID from the database if exists

    names: List[Literal] = []

    addresses: List[StructuredPhysicalAddress] = []

    places: List[Place] = []

    identifiers: List[OrganizationIdentifier] = []

    @field_validator('identifiers', mode="after")
    @classmethod
    def _validate_identifiers(cls, identifiers):
        return cls._deduplicate_identifiers(identifiers)

    def get_name(self, language: str) -> Optional[Literal]:
        """
        Get the name in the given language.
        :param language: Language code
        :return: Name or None if not found
        """
        return next((name for name in self.names if name.language == language), None)
