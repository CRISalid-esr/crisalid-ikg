"""
Person model
"""

from typing import List, Optional, Annotated

from loguru import logger
from pydantic import BeforeValidator, Field, field_validator, model_validator

from app.models.agent_identifiers import PersonIdentifier
from app.models.agents import Agent
from app.models.employments import Employment
from app.models.identifier_types import PersonIdentifierType
from app.models.memberships import Membership
from app.models.people_names import PersonName


def _hydrate_memberships(v):
    if isinstance(v, dict) and 'entity' in v:
        return Membership(**v)
    return v


def _hydrate_employments(v):
    if isinstance(v, dict) and 'entity' in v:
        return Employment(**v)
    return v


ImportMembership = Annotated[Membership, BeforeValidator(_hydrate_memberships)]
ImportEmployment = Annotated[Employment, BeforeValidator(_hydrate_employments)]


class Person(Agent[PersonIdentifierType]):
    """
    Person API model
    """

    uid: Optional[str] = None

    display_name: str

    display_name_variants: Optional[List[str]] = []

    names: Optional[List[PersonName]] = []

    identifiers: Optional[List[PersonIdentifier]] = []

    memberships: Optional[List[ImportMembership]] = Field(default_factory=list)

    employments: Optional[List[ImportEmployment]] = Field(default_factory=list)

    external: bool = False

    @field_validator("identifiers", mode="after")
    @classmethod
    def _validate_identifiers(cls, identifiers):
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

        return cls._deduplicate_identifiers(valid_identifiers)

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
        Validates and ensures a display name is present.
        If no display_name is provided, build it from the first available person name:
        "last_name, first_name".
        """
        if not values.get("display_name"):
            names = values.get("names", [])

            if not names or not isinstance(names, list) or not names:
                raise ValueError(
                    "Either a display_name or at least one person name "
                    "with a last name or first name must be provided.")

            # Extract the first person name
            name = names[0]
            name = name.model_dump() if isinstance(name, PersonName) else name

            # Ensure we have at least a last name or a first name
            last_name = name.get("last_names", [{}])
            last_name = last_name[0].get("value") if (last_name
                                                      and isinstance(last_name,
                                                                     list)
                                                      and last_name) else None

            first_name = name.get("first_names", [{}])
            first_name = first_name[0].get("value") if (first_name
                                                        and isinstance(first_name,
                                                                       list)
                                                        and first_name) else None

            if not last_name and not first_name:
                raise ValueError(
                    "The provided person name must have at least a last name or a first name.")

            # Build the display name from available parts
            values["display_name"] = " ".join(filter(None, [first_name, last_name]))

        return values

    def get_first_name(self):
        """
        Get the first name of the person, or a blank string if not found
        :return: first name
        """
        if not self.names:
            return ""
        first_name = self.names[0].first_names
        if not first_name:
            return ""
        return first_name[0].value

    def get_last_name(self):
        """
        Get the last name of the person, or a blank string if not found
        :return: last name
        """
        if not self.names:
            return ""
        last_name = self.names[0].last_names
        if not last_name:
            return ""
        return last_name[0].value
