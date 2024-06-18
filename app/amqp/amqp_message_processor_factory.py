import asyncio

import aio_pika

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_people_message_processor import AMQPPeopleMessageProcessor
from app.amqp.amqp_publication_message_processor import AMQPPublicationMessageProcessor
from app.settings.app_settings import AppSettings


class AMQPMessageProcessorFactory:
    @staticmethod
    def get_processor(
            topic: str,
            exchange: aio_pika.Exchange,
            tasks_queue: asyncio.Queue,
            settings: AppSettings
    ) -> AMQPMessageProcessor:
        if topic == settings.amqp_publications_topic:
            return AMQPPublicationMessageProcessor(exchange, tasks_queue, settings)
        elif topic == settings.amqp_people_topic:
            return AMQPPeopleMessageProcessor(exchange, tasks_queue, settings)
        else:
            raise ValueError(f"No processor found for topic: {topic}")
