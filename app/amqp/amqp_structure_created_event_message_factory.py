from typing import Any

from app.amqp.amqp_structure_event_message_factory import AMQPStructureEventMessageFactory


class AMQPStructureCreatedEventMessageFactory(AMQPStructureEventMessageFactory):
    """Factory for structure created events."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_research_unit_event_created_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        structure_uid = self.content.get("structure_uid")
        fields = await self._build_structure_message_payload(structure_uid)
        structure_type = fields.pop("generic_type")
        return {"type": structure_type, "event": "created", "fields": fields}
