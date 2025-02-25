from typing import Any

from app.amqp.amqp_research_structure_event_message_factory import \
    AMQPResearchStructureEventMessageFactory


class AMQPResearchStructureDeletedEventMessageFactory(AMQPResearchStructureEventMessageFactory):
    """Factory for building AMQP messages related to research structures deleted events."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_resarch_structure_event_deleted_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        research_structure_uid = self.content.get("research_structure_uid")
        return {
            "type": "research_structure",
            "event": "deleted",
            "fields": await self._build_research_structure_message_payload(research_structure_uid)

        }
