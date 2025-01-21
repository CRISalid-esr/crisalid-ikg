import json
from enum import Enum

import aio_pika
from aio_pika import DeliveryMode
from loguru import logger

from app.amqp.amqp_document_created_event_message_factory import \
    AMQPDocumentCreatedEventMessageFactory
from app.amqp.amqp_document_deleted_event_message_factory import \
    AMQPDocumentDeletedEventMessageFactory
from app.amqp.amqp_document_unchanged_event_message_factory import \
    AMQPDocumentUnchangedEventMessageFactory
from app.amqp.amqp_document_updated_event_message_factory import \
    AMQPDocumentUpdatedEventMessageFactory
from app.amqp.amqp_person_created_event_message_factory import AMQPPersonCreatedEventMessageFactory
from app.amqp.amqp_person_updated_event_message_factory import AMQPPersonUpdatedEventMessageFactory
from app.amqp.amqp_publication_retrieval_message_factory import \
    AMQPPublicationRetrievalMessageFactory
from app.amqp.amqp_research_structure_created_event_message_factory import \
    AMQPResearchStructureCreatedEventMessageFactory
from app.amqp.amqp_research_structure_deleted_event_message_factory import \
    AMQPResearchStructureDeletedEventMessageFactory
from app.amqp.amqp_research_structure_unchanged_event_message_factory import \
    AMQPResearchStructureUnchangedEventMessageFactory
from app.amqp.amqp_research_structure_updated_event_message_factory import \
    AMQPResearchStructureUpdatedEventMessageFactory


class AMQPMessagePublisher:
    """Rabbitmq Publisher abstraction"""

    # enum MessageTypes with values : Task, Event
    # enum MessageSubtype with value : PUBLICATION_RETRIEVAL

    class MessageType(Enum):
        """
        Types of emited AMQP messages (Event or Task)
        """
        TASK = "Task"
        EVENT = "Event"

    class MessageSubtype(Enum):
        """
        Subtypes of Messages
        """

    class TaskMessageSubtype(MessageSubtype):
        """
        Subtypes of Task messages
        """
        PUBLICATION_RETRIEVAL = "Publication retrieval"
        PERSON_EVENT = "Person event"

    class EventMessageSubtype(MessageSubtype):
        """
        Subtypes of Event messages
        """
        PERSON_CREATED = "Person created"
        PERSON_UPDATED = "Person updated"
        STRUCTURE_CREATED = "Structure created"
        STRUCTURE_UPDATED = "Structure updated"
        STRUCTURE_DELETED = "Structure deleted"
        STRUCTURE_UNCHANGED = "Structure unchanged"
        DOCUMENT_UPDATED = "Document updated"
        DOCUMENT_CREATED = "Document created"
        DOCUMENT_DELETED = "Document deleted"
        DOCUMENT_UNCHANGED = "Document unchanged"

    MESSAGE_FACTORIES = {
        MessageType.TASK: {
            TaskMessageSubtype.PUBLICATION_RETRIEVAL: AMQPPublicationRetrievalMessageFactory,
        },
        MessageType.EVENT: {
            EventMessageSubtype.PERSON_CREATED: AMQPPersonCreatedEventMessageFactory,
            EventMessageSubtype.PERSON_UPDATED: AMQPPersonUpdatedEventMessageFactory,
            EventMessageSubtype.STRUCTURE_CREATED: AMQPResearchStructureCreatedEventMessageFactory,
            EventMessageSubtype.STRUCTURE_UPDATED: AMQPResearchStructureUpdatedEventMessageFactory,
            EventMessageSubtype.STRUCTURE_UNCHANGED:
                AMQPResearchStructureUnchangedEventMessageFactory,
            EventMessageSubtype.STRUCTURE_DELETED: AMQPResearchStructureDeletedEventMessageFactory,
            EventMessageSubtype.DOCUMENT_CREATED: AMQPDocumentCreatedEventMessageFactory,
            EventMessageSubtype.DOCUMENT_UPDATED: AMQPDocumentUpdatedEventMessageFactory,
            EventMessageSubtype.DOCUMENT_DELETED: AMQPDocumentDeletedEventMessageFactory,
            EventMessageSubtype.DOCUMENT_UNCHANGED: AMQPDocumentUnchangedEventMessageFactory,
        },
    }

    def __init__(self, exchange: aio_pika.Exchange):
        """Init AMQP Publisher class"""
        self.exchange = exchange

    async def publish(self, message_type: MessageType, message_subtype: MessageSubtype,
                      content: dict) -> None:
        """Publish a message to the AMQP queue"""
        payload, routing_key = await self._build_message(message_type, message_subtype, content)
        if routing_key is None:
            return
        try:
            message = aio_pika.Message(
                json.dumps(payload, default=str).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
            )

            await self.exchange.publish(
                message=message,
                routing_key=routing_key,
            )
            logger.debug(f"Message published to graph exchange with {routing_key} topic :"
                         f" {payload}")
        except aio_pika.exceptions.AMQPError as e:
            logger.error(f"Error publishing message to {routing_key} queue : {e}")

    @classmethod
    async def _build_message(cls, message_type: MessageType,
                             message_subtype: MessageSubtype,
                             content: dict) -> tuple[str | None, str | None]:
        factories = cls.MESSAGE_FACTORIES.get(message_type)
        if factories is None:
            logger.error(f"Message type {message_type} not supported")
            return None, None

        factory_cls = factories.get(message_subtype)
        if factory_cls is None:
            logger.error(f"Message subtype {message_subtype} not supported for type {message_type}")
            return None, None

        return await factory_cls(content).build_message()
