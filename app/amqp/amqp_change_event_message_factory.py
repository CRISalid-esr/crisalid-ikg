from abc import abstractmethod
from typing import Any

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory


class AMQPChangeEventMessageFactory(AbstractAMQPMessageFactory):
    """
    Base factory for AMQP messages reporting the outcome of a user-action change.

    The payload is built purely from the pre-computed ``fields`` dict carried by the
    change signals (see ``Change.to_event_fields``) — no database round-trip.
    """

    async def _build_payload(self) -> dict[str, Any]:
        return {
            "type": "change",
            "event": self._event_name(),
            "fields": self.content.get("fields"),
        }

    @abstractmethod
    def _event_name(self) -> str:  # pragma: no cover
        raise NotImplementedError()
