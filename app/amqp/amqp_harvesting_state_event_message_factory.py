from typing import Any

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory


class AMQPHarvestingStateEventMessageFactory(AbstractAMQPMessageFactory):
    """
    Factory for forwarding harvesting state event messages without modification.
    """

    async def _build_payload(self) -> dict[str, Any]:
        return {"type": "harvesting_state_event",
                "fields": self.content}

    def _build_routing_key(self) -> str:
        assert self.content["state"] in ["running", "completed", "failed"]
        return self.settings.amqp_graph_harvesting_state_event_routing_key.replace(
            "*", self.content["state"])
