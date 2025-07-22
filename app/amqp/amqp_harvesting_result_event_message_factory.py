from typing import Any

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory


class AMQPHarvestingResultEventMessageFactory(AbstractAMQPMessageFactory):
    """
    Factory for forwarding harvesting result event messages without modification.
    """

    async def _build_payload(self) -> dict[str, Any]:
        return {"type": "harvesting_result_event",
                "fields": self.content}

    def _build_routing_key(self) -> str:
        assert self.content["reference_event"]["type"] in ["created", "updated", "unchanged",
                                                           "deleted"]
        return self.settings.amqp_graph_harvesting_result_event_routing_key.replace(
            "*", self.content["reference_event"]["type"]
        )
