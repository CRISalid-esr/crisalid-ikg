from typing import List

from pydantic import BaseModel

from app.config import get_app_settings
from app.models.agent_identifiers import AgentIdentifier, PersonIdentifier, OrganizationIdentifier
from app.models.identifier_types import AgentIdentifierType, PersonIdentifierType, \
    OrganizationIdentifierType


class AgentIdentifierService:
    """
    Service to handle
    """
    IDENTIFIER_SEPARATOR = "-"

    @classmethod
    def compute_uid_for(cls, entity: BaseModel) -> str:
        """
        Compute an ID based on the first identifier type in the given order.
        :param entity: The entity to compute the ID for.
        :return: The computed ID.
        :raises ValueError: If the first identifier type in the order is not found.
        """
        identifier_order = cls._get_identifier_order(entity.__class__)

        first_identifier_type = identifier_order[0]

        selected_identifier = next(
            (identifier for identifier in entity.identifiers
             if identifier.type == first_identifier_type), None)

        if selected_identifier is None:
            raise ValueError(
                f"Identifier of type {first_identifier_type} not found in data : {entity.dict()}.")

        return f"{selected_identifier.type.value}" \
               f"{cls.IDENTIFIER_SEPARATOR}" \
               f"{selected_identifier.value}"

    @classmethod
    def compute_identifier_from_uid(cls, entity_cls, unique_id: str) -> AgentIdentifier:
        """
        Compute an identifier from a unique ID.
        :param unique_id: The unique ID.
        :return: The computed identifier.
        """
        if cls.IDENTIFIER_SEPARATOR not in unique_id:
            raise ValueError(f"Invalid unique ID format: {unique_id}")
        identifier_type, identifier_value = unique_id.split(cls.IDENTIFIER_SEPARATOR, 1)
        if entity_cls.__name__ == "Person":
            return PersonIdentifier(type=PersonIdentifierType(identifier_type),
                                    value=identifier_value)
        if entity_cls.__name__ == "ResearchStructure":
            return OrganizationIdentifier(type=OrganizationIdentifierType(identifier_type),
                                          value=identifier_value)
        raise ValueError(f"No identifier type defined for {entity_cls.__name__}.")

    @staticmethod
    def identifiers_are_identical(identifiers_1: list[AgentIdentifier],
                                  identifiers_2: list[AgentIdentifier]) -> bool:
        """
        Compare two lists of agent identifiers to check identity
        :param identifiers_1:
        :param identifiers_2:
        :return:
        """
        identifiers_1 = sorted(identifiers_1, key=lambda x: str(x.type))
        identifiers_2 = sorted(identifiers_2, key=lambda x: str(x.type))
        return identifiers_1 != identifiers_2

    @classmethod
    def _get_identifier_order(cls, entity_cls) -> List[AgentIdentifierType]:
        """
        Get the order of identifier types to prioritize when computing an ID.
        :return: The list of identifier types.
        """
        settings = get_app_settings()
        # check with string comparison to avoid circular imports
        if entity_cls.__name__ == "Person":
            return settings.person_identifier_order
        if entity_cls.__name__ == "ResearchStructure":
            return settings.research_structure_identifier_order
        raise ValueError(f"No identifier order defined for {entity_cls.__name__}.")
