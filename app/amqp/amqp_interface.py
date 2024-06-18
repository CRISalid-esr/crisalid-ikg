import asyncio
from collections import defaultdict
from typing import List

import aio_pika
from aio_pika import ExchangeType

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_message_processor_factory import AMQPMessageProcessorFactory
from app.amqp.amqp_publication_message_processor import AMQPPublicationMessageProcessor
from app.settings.app_settings import AppSettings

DEFAULT_RESULT_TIMEOUT = 600


# pylint: disable=too-many-instance-attributes
class AMQPInterface:
    """Rabbitmq Connexion abstraction"""

    INNER_PUBLICATIONS_TASKS_QUEUE_LENGTH = 10000

    def __init__(self, settings: AppSettings):
        """Init AMQP Connexion class"""
        self.settings = settings
        self.pika_queues: dict[str, aio_pika.Queue] = {}
        self.pika_channel: aio_pika.Channel | None = None
        self.pika_exchanges: dict[str, aio_pika.Exchange] = {}
        self.pika_connexion: aio_pika.abc.AbstractRobustConnection | None = None
        self.inner_tasks_queues: dict[str, asyncio.Queue] = {}
        self.message_processing_workers: dict[str, List[asyncio.Task]] = defaultdict(list)
        self.keys = {
            "people": [self.settings.amqp_people_event_routing_key],
            "publications": [self.settings.amqp_reference_event_routing_key],
        }

    async def connect(self):
        """Connect to AMQP queue"""
        await self._connect()
        await self._declare_exchange(self.settings.amqp_people_topic, self.settings.amqp_directory_exchange_name)
        await self._declare_exchange(self.settings.amqp_publications_topic,
                                     self.settings.amqp_publications_exchange_name)
        await self._attach_message_processing_workers(self.settings.amqp_people_topic)
        await self._attach_message_processing_workers(self.settings.amqp_publications_topic)
        await self._bind_queue(self.settings.amqp_people_topic, self.settings.amqp_people_queue_name)
        await self._bind_queue(self.settings.amqp_publications_topic, self.settings.amqp_publications_queue_name)

    async def listen(self, topic: str) -> None:
        """Listen to AMQP queue"""
        await self._listen_to_messages(topic)

    async def stop_listening(self) -> None:
        """Stop listening to AMQP queue"""
        try:
            await asyncio.wait_for(
                self.inner_tasks_queues.join(),
                timeout=self.settings.amqp_wait_before_shutdown,
            )
        finally:
            for worker in self.message_processing_workers:
                worker.cancel()
            await self.pika_channel.close()
            await self.pika_connexion.close()

    async def _attach_message_processing_workers(self, topic: str):
        self.inner_tasks_queues[topic] = asyncio.Queue(maxsize=self.INNER_PUBLICATIONS_TASKS_QUEUE_LENGTH)
        for worker_id in range(self.settings.amqp_task_parallelism_limit):
            processor = await self._message_processor(topic)
            self.message_processing_workers[topic].append(
                asyncio.create_task(
                    processor.wait_for_message(worker_id),
                    name=f"amqp_message_processor_{worker_id}",
                )
            )

    async def _message_processor(self, topic: str) -> AMQPMessageProcessor:
        return AMQPMessageProcessorFactory.get_processor(topic, self.pika_exchanges[topic],
                                                         self.inner_tasks_queues[topic],
                                                         self.settings)

    async def _listen_to_messages(self, topic: str):
        async with self.pika_queues[topic].iterator() as queue_iter:
            async for message in queue_iter:
                await self.inner_tasks_queues[topic].put(message)

    async def _declare_exchange(self, topic: str, exchange_name: str) -> None:
        """
        Declare the publication exchange
        :param exchange_name: exchange name
        :return: None
        """
        self.pika_exchanges[topic] = await self.pika_channel.declare_exchange(
            exchange_name,
            ExchangeType.TOPIC,
        )

    async def _bind_queue(self, topic: str, queue_name: str) -> None:
        # Bind service message queue to publication exchange
        self.pika_queues[topic] = await self.pika_channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-consumer-timeout": self.settings.amqp_consumer_ack_timeout},
        )
        for key in self.keys[topic]:
            await self.pika_queues[topic].bind(self.pika_exchanges[topic],
                                               routing_key=key)

    async def _connect(self) -> None:
        self.pika_connexion: aio_pika.Connection = await aio_pika.connect_robust(
            f"amqp://{self.settings.amqp_user}:"
            f"{self.settings.amqp_password}"
            f"@{self.settings.amqp_host}/",
        )
        self.pika_channel = await self.pika_connexion.channel(publisher_confirms=True)
        await self.pika_channel.set_qos(
            prefetch_count=self.settings.amqp_prefetch_count
        )
