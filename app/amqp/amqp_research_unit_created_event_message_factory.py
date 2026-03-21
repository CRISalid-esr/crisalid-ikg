from typing import Any

from app.amqp.amqp_research_unit_event_message_factory import \
    AMQPResearchUnitEventMessageFactory


class AMQPResearchUnitCreatedEventMessageFactory(AMQPResearchUnitEventMessageFactory):
    """Factory for building AMQP messages related to research structures created events."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_research_unit_event_created_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        research_unit_uid = self.content.get("research_unit_uid")
        return {
            "type": "research_unit",
            "event": "created",
            "fields": await self._build_research_unit_message_payload(research_unit_uid)
        }
