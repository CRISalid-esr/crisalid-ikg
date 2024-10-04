"""
Person model
"""

import re
from typing import List, Optional, Annotated

from pydantic import field_validator, BeforeValidator, Field

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

    uid: Optional[str] = None  # uid from the database if exists

    names: List[PersonName] = []

    identifiers: List[PersonIdentifier]

    memberships: List[ImportMembership] = Field(default_factory=list)

    @field_validator("identifiers", mode="after")
    @staticmethod
    def _validate_identifiers(identifiers):
        if identifiers and any(
                ident.type not in PersonIdentifierType for ident in identifiers
        ):
            raise ValueError(
                "All identifiers for a Person must be of type PersonIdentifierType"
            )

        type_pattern = {
            PersonIdentifierType.ORCID: "^([0-9]{4}-){3}[0-9]{3}[0-9X]$",
            PersonIdentifierType.IDREF: "^[0-9]{1,9}$",
            PersonIdentifierType.ID_HAL_S: "^([a-z]+-)*[a-z]+$",
            PersonIdentifierType.ID_HAL_I: "^[0-9]{1,9}$",
            PersonIdentifierType.SCOPUS_EID: "^[0-9]+$",
        }
        for identifier in identifiers:
            if identifier.type != PersonIdentifierType.LOCAL:
                if identifier.type in type_pattern:
                    pattern = type_pattern[identifier.type]
                    if not re.fullmatch(pattern, identifier.value):
                        raise ValueError(
                            f"Value {identifier.value} for"
                            f" {identifier.type} does not match the expected pattern {pattern}"
                        )

        Person._prevent_duplicate_identifiers(identifiers)

        return identifiers

    def get_identifier(self, identifier_type: PersonIdentifierType) -> PersonIdentifier:
        """
        Get the identifier of the given type
        :param identifier_type: identifier type
        :return: identifier
        """
        return next((ident for ident in self.identifiers if ident.type == identifier_type), None)
