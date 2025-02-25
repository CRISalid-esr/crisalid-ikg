from typing import Any

from app.amqp.amqp_document_event_message_factory import AMQPDocumentEventMessageFactory


class AMQPDocumentDeletedEventMessageFactory(AMQPDocumentEventMessageFactory):
    """Factory for building AMQP messages related to research structures created events."""

    def _build_routing_key(self) -> str:
        return self.settings.amqp_graph_document_event_deleted_routing_key

    async def _build_payload(self) -> dict[str, Any]:
        document_uid = self.content.get("document_uid")
        return {
            "type": "document",
            "event": "deleted",
            "fields": await self._build_document_message_payload(document_uid)

        }
