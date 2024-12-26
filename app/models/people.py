"""
Person model
"""

from typing import List, Optional, Annotated

from loguru import logger
from pydantic import BeforeValidator, Field, field_validator, model_validator

from app.models.agent_identifiers import PersonIdentifier
from app.models.agents import Agent
from app.models.identifier_types import PersonIdentifierType
from app.models.memberships import Membership
from app.models.people_names import PersonName


def _hydrate_memberships(v):
    if isinstance(v, dict) and 'entity' in v:
        return Membership(**v)
    return v


ImportMembership = Annotated[Membership, BeforeValidator(_hydrate_memberships)]


class Person(Agent[PersonIdentifierType]):
    """
    Person API model
    """

    uid: Optional[str] = None

    display_name: str

    names: Optional[List[PersonName]] = []

    identifiers: Optional[List[PersonIdentifier]] = []

    memberships: Optional[List[ImportMembership]] = Field(default_factory=list)

    external: bool = False

    @field_validator("identifiers", mode="after")
    @staticmethod
    def _validate_identifiers(identifiers):
        valid_identifiers = []
        for identifier in (identifiers or []):
            if not PersonIdentifierType.validate_identifier(identifier.type, identifier.value):
                logger.warning(
                    f"Invalid identifier with type {identifier.type} and value {identifier.value}"
                )
                continue
            if not PersonIdentifierType.validate_identifier(identifier.type, identifier.value):
                logger.warning(
                    "Invalid identifier with type "
                    f"{str(identifier.type)} and value {identifier.value}"
                )
                continue

            valid_identifiers.append(identifier)

        Person._prevent_duplicate_identifiers(valid_identifiers)

        return valid_identifiers

    def get_identifier(self, identifier_type: PersonIdentifierType) -> PersonIdentifier:
        """
        Get the identifier of the given type
        :param identifier_type: identifier type
        :return: identifier
        """
        return next((ident for ident in self.identifiers if ident.type == identifier_type), None)

    @model_validator(mode="before")
    @classmethod
    def _build_display_name(cls, values):
        """
        If no display_name is provided, build it from the first name : "last_name, first_name"
        """
        if "display_name" not in values or not values["display_name"]:
            name = values.get("names")[0]
            # If the name is a PersonName object, model_dump
            name = name.model_dump() if isinstance(name, PersonName) else name
            values["display_name"] = (f"{name['last_names'][0]['value']}, "
                                      f"{name['first_names'][0]['value']}")
        return values
