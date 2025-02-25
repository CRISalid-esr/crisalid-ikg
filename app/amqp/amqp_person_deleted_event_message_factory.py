from typing import Any

from app.amqp.amqp_person_event_message_factory import AMQPPersonEventMessageFactory


class AMQPPersonDeletedEventMessageFactory(AMQPPersonEventMessageFactory):
    """Factory for building AMQP messages related to people unchanged events."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_people_event_deleted_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        person_uid = self.content.get("person_uid")
        return {
            "type": "person",
            "event": "deleted",
            "fields": await self._build_person_message_payload(person_uid)
        }
