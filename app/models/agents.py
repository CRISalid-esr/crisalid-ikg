"""
Agent model
"""
from typing import List, Generic

from pydantic import BaseModel

from app.models.agent_identifiers import AgentIdentifier
from app.models.shared_types import IdType


class Agent(BaseModel, Generic[IdType]):
    """
    Agent API object
    """

    # at least one identifier is required
    identifiers: List[AgentIdentifier[IdType]]
