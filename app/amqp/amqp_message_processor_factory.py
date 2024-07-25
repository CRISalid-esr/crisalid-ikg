import asyncio

import aio_pika

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_people_message_processor import AMQPPeopleMessageProcessor
from app.amqp.amqp_publication_message_processor import AMQPPublicationMessageProcessor
from app.amqp.amqp_structure_message_processor import AMQPStructureMessageProcessor
from app.settings.app_settings import AppSettings


class AMQPMessageProcessorFactory:
    """
    Factory to create AMQP message processor adapted to the message topic
    """

    @staticmethod
    def get_processor(
            topic: str,
            exchange: aio_pika.Exchange,
            tasks_queue: asyncio.Queue,
            settings: AppSettings
    ) -> AMQPMessageProcessor:
        """
        Get the appropriate processor for the given topic
        :param topic:
        :param exchange:
        :param tasks_queue:
        :param settings:
        :return:
        """
        if topic == settings.amqp_publications_topic:
            return AMQPPublicationMessageProcessor(exchange, tasks_queue, settings)
        if topic == settings.amqp_people_topic:
            return AMQPPeopleMessageProcessor(exchange, tasks_queue, settings)
        if topic == settings.amqp_structures_topic:
            return AMQPStructureMessageProcessor(exchange, tasks_queue, settings)
        raise ValueError(f"No processor found for topic: {topic}")
