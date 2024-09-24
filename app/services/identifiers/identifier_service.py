from typing import List

from pydantic import BaseModel

from app.config import get_app_settings
from app.models.agent_identifiers import AgentIdentifier
from app.models.identifier_types import AgentIdentifierType
from app.models.people import Person
from app.models.research_structures import ResearchStructure


class AgentIdentifierService:
    """
    Service to handle
    """
    IDENTIFIER_SEPARATOR = "-"

    @classmethod
    def compute_identifier_for(cls, entity: BaseModel) -> str:
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
        if entity_cls is Person:
            return settings.person_identifier_order
        if entity_cls is ResearchStructure:
            return settings.research_structure_identifier_order
        raise ValueError(f"No identifier order defined for {entity_cls.__name__}.")
