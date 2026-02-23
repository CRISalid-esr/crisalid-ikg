from abc import ABC, abstractmethod
from typing import Any

from app.config import get_app_settings


class AbstractAMQPMessageFactory(ABC):
    """Abstract factory for building AMQP messages."""

    def __init__(self, content):
        self.content = content
        self.settings = get_app_settings()

    async def build_message(self) -> tuple[dict[str, Any] | None, str | None]:
        """Build the message routing key and payload."""
        return await self._build_payload(), self._build_routing_key()

    @abstractmethod
    def _build_routing_key(self) -> str | None:  # pragma: no cover
        raise NotImplementedError()

    @abstractmethod
    async def _build_payload(self) -> dict[str, Any] | None:  # pragma: no cover
        raise NotImplementedError()
