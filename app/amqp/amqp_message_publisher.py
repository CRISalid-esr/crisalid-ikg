import json
from enum import Enum

import aio_pika
from aio_pika import DeliveryMode
from loguru import logger

from app.amqp.amqp_publication_retrieval_message_factory import \
    AMQPPublicationRetrievalMessageFactory

DEFAULT_RESULT_TIMEOUT = 600


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

    class EventMessageSubtype(MessageSubtype):
        """
        Subtypes of Event messages
        """

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
        except Exception as e:
            logger.error(f"Error publishing message to {routing_key} queue : {e}")
            return
        logger.debug(f"Message published to {routing_key} queue : {payload}")

    @staticmethod
    async def _build_message(message_type: MessageType,
                             message_subtype: MessageSubtype,
                             content: dict) -> tuple[str | None, str | None]:
        if message_type is AMQPMessagePublisher.MessageType.TASK:
            if message_subtype is AMQPMessagePublisher.TaskMessageSubtype.PUBLICATION_RETRIEVAL:
                return await AMQPPublicationRetrievalMessageFactory(content).build_message()
        return None, None
