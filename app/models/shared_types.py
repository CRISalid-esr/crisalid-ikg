from typing import TypeVar

from app.models.identifier_types import AgentIdentifierType

IdType = TypeVar("IdType", bound=AgentIdentifierType) # pylint: disable=invalid-name
