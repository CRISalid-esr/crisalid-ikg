"""
Agent model
"""
from typing import List, Generic

from pydantic import BaseModel

from app.models.agent_identifiers import AgentIdentifier
from app.models.shared_types import IdType


class Agent(BaseModel, Generic[IdType]):
    """
    Agent API model (equivalent to Foaf Agent)
    """

    # at least one identifier is required
    identifiers: List[AgentIdentifier[IdType]]

    def get_identifier(self, identifier_type: IdType) -> AgentIdentifier[IdType]:
        """
        Get the identifier of the given type
        :param identifier_type: identifier type
        :return: identifier
        """
        return next((ident for ident in self.identifiers if ident.type == identifier_type), None)
