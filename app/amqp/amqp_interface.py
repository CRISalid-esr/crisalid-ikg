import asyncio
from collections import defaultdict
from typing import List
from urllib.parse import quote

import aio_pika
from aio_pika import ExchangeType
from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_message_processor_factory import AMQPMessageProcessorFactory
from app.amqp.amqp_message_publisher import AMQPMessagePublisher
from app.settings.app_settings import AppSettings


# pylint: disable=too-many-instance-attributes
class AMQPInterface:
    """Rabbitmq Connexion abstraction"""

    INNER_TASKS_QUEUE_LENGTH = 10000

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
            "people": [self.settings.amqp_directory_people_event_routing_key],
            "structures": [self.settings.amqp_directory_structure_event_routing_key],
            "publications": [self.settings.amqp_harvester_reference_event_routing_key],
            "harvesting_events": [self.settings.amqp_harvesting_event_routing_key],
            "user_actions": [self.settings.amqp_graph_document_task_routing_key,
                             self.settings.amqp_graph_person_documents_fetch_task_routing_key,
                             self.settings.amqp_graph_person_attribute_update_task_routing_key],
        }

    async def connect(self, listen=True) -> None:
        """Connect to AMQP queue"""
        logger.info("Connecting to AMQP broker...")
        await self._connect()
        logger.info("Connected to AMQP broker")

        logger.info("Declaring exchanges...")
        await self._declare_exchange(self.settings.amqp_graph_exchange_name, with_dlx=True)
        await self._declare_exchange(self.settings.amqp_publications_exchange_name)

        if not listen:
            logger.info("Connection established in non-listening mode.")
            return

        await self._declare_exchange(self.settings.amqp_directory_exchange_name)

        logger.info("Binding queues...")
        await self._bind_queue(self.settings.amqp_directory_exchange_name,
                               self.settings.amqp_people_topic,
                               self.settings.amqp_people_queue_name)
        await self._bind_queue(self.settings.amqp_directory_exchange_name,
                               self.settings.amqp_structures_topic,
                               self.settings.amqp_structures_queue_name)
        await self._bind_queue(self.settings.amqp_publications_exchange_name,
                               self.settings.amqp_publications_topic,
                               self.settings.amqp_publications_queue_name)
        await self._bind_queue(self.settings.amqp_publications_exchange_name,
                               self.settings.amqp_harvesting_events_topic,
                               self.settings.amqp_harvesting_events_queue_name)
        await self._bind_queue(self.settings.amqp_graph_exchange_name,
                               self.settings.amqp_user_actions_topic,
                               self.settings.amqp_user_actions_queue_name,
                               with_dlq=True)

        logger.info("Attaching message processing workers...")
        self._attach_message_processing_workers(self.settings.amqp_people_topic)
        self._attach_message_processing_workers(self.settings.amqp_publications_topic)
        self._attach_message_processing_workers(self.settings.amqp_structures_topic)
        self._attach_message_processing_workers(self.settings.amqp_user_actions_topic)
        self._attach_message_processing_workers(self.settings.amqp_harvesting_events_topic)

        logger.info("AMQP interface setup complete")

    async def stop_listening(self) -> None:
        """Stop listening to AMQP queue"""
        logger.info("Stopping AMQP listeners and workers...")
        try:
            for topic, queue in self.inner_tasks_queues.items():
                logger.info(f"Waiting for tasks in queue '{topic}' to complete...")
                await asyncio.wait_for(
                    queue.join(),
                    timeout=self.settings.amqp_wait_before_shutdown,
                )
        finally:
            logger.info("Cancelling worker tasks...")
            for workers in self.message_processing_workers.values():
                for worker in workers:
                    logger.info(f"Cancelling worker: {worker.get_name()}")
                    worker.cancel()

            logger.info("Closing AMQP channel and connection...")
            await self.pika_channel.close()
            await self.pika_connexion.close()

        logger.info("AMQP listeners and workers stopped.")

    def _attach_message_processing_workers(self, topic: str):
        logger.info(f"Attaching message processing workers for topic: {topic}")
        self.inner_tasks_queues[topic] = asyncio.Queue(
            maxsize=self.INNER_TASKS_QUEUE_LENGTH)
        for worker_id in range(self.settings.amqp_task_parallelism_limit):
            self._attach_message_processing_worker(topic, worker_id)

    def _attach_message_processing_worker(self, topic, worker_id):
        logger.info(f"Creating message processor for worker {worker_id} on topic: {topic}")
        processor = self._message_processor(topic)
        task = asyncio.create_task(
            processor.wait_for_message(worker_id),
            name=f"amqp_message_processor_{topic}_{worker_id}",
        )
        self.message_processing_workers[topic].append(task)

    def _message_processor(self, topic: str) -> AMQPMessageProcessor:
        return AMQPMessageProcessorFactory.get_processor(topic,
                                                         self.inner_tasks_queues[topic])

    async def listen(self, topic: str) -> None:
        """
        Listen to AMQP queue
        :param topic: topic to listen to
        :return: None
        """
        logger.info(f"Starting to listen on topic: {topic}")
        try:
            async with self.pika_queues[topic].iterator() as queue_iter:
                async for message in queue_iter:
                    queue_size = self.inner_tasks_queues[topic].qsize()
                    logger.debug(f"Received message: {message.body}")
                    logger.debug(f"Number of messages in queue before adding :"
                                 f" {queue_size}")
                    if queue_size == self.settings.amqp_prefetch_count - 2:
                        logger.warning(f"Queue for topic '{topic}' is almost full. "
                                       f"Attaching a new worker to process messages.")
                        self._attach_message_processing_worker(
                            topic,
                            len(
                                self.message_processing_workers[
                                    topic]) + 1)
                    await self.inner_tasks_queues[topic].put(message)
                    await asyncio.sleep(0)
                    logger.debug(f"Number of messages in queue after adding :"
                                 f" {self.inner_tasks_queues[topic].qsize()}")
                    logger.debug(f"Message added to inner queue for topic: {topic}")
        # pylint: disable=broad-except
        except Exception as e:
            logger.error(f"Error while listening to messages on topic '{topic}': {e}",
                         exc_info=True)

    async def _declare_exchange(self, exchange_name: str, with_dlx=False) -> None:
        if exchange_name in self.pika_exchanges:
            logger.info(f"Exchange {exchange_name} already declared, skipping.")
            return
        if with_dlx:
            logger.info(f"Declaring exchange with dead-letter support: {exchange_name}")
            dlx_exchange_name = f"dlx.{exchange_name}"
            if dlx_exchange_name not in self.pika_exchanges:
                logger.info(f"Declaring dead-letter exchange: {dlx_exchange_name}")
                self.pika_exchanges[dlx_exchange_name] = await self.pika_channel.declare_exchange(
                    dlx_exchange_name,
                    ExchangeType.TOPIC,
                    durable=True,
                )
                logger.info(f"Dead-letter exchange declared: {dlx_exchange_name}")
            logger.info(f"Declaring exchange with dead-letter support: {exchange_name}")
            self.pika_exchanges[exchange_name] = await self.pika_channel.declare_exchange(
                exchange_name,
                ExchangeType.TOPIC,
                durable=True,
            )
            return
        logger.info(f"Declaring exchange: {exchange_name}")
        self.pika_exchanges[exchange_name] = await self.pika_channel.declare_exchange(
            exchange_name,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info(f"Exchange declared: {exchange_name}")

    async def _bind_queue(self, exchange_name: str,
                          topic: str, queue_name: str, with_dlq=False) -> None:
        logger.info(
            f"Declaring and binding queue '{queue_name}' "
            f"to exchange '{exchange_name}' with topic '{topic}'")

        queue_arguments = {
            "x-consumer-timeout": self.settings.amqp_consumer_ack_timeout,
        }

        if with_dlq:
            queue_arguments["x-dead-letter-exchange"] = f"dlx.{exchange_name}"
            queue_arguments["x-dead-letter-routing-key"] = topic

        self.pika_queues[topic] = await self.pika_channel.declare_queue(
            queue_name,
            durable=True,
            arguments=queue_arguments,
        )

        for key in self.keys[topic]:
            await self.pika_queues[topic].bind(self.pika_exchanges[exchange_name], routing_key=key)

        logger.info(f"Queue '{queue_name}' bound to exchange '{exchange_name}'")

        if with_dlq:
            dlq_name = f"dlq.{queue_name}"
            dlx_key = f"dlx.{topic}"
            self.pika_queues[dlx_key] = await self.pika_channel.declare_queue(
                dlq_name,
                durable=True,
                arguments={"x-consumer-timeout": self.settings.amqp_consumer_ack_timeout},
            )
            await self.pika_queues[dlx_key].bind(self.pika_exchanges[f"dlx.{exchange_name}"],
                                                 routing_key="#")
            logger.info(f"Dead-letter queue '{dlq_name}' bound to DLX '{f'dlx.{exchange_name}'}'")

    async def _connect(self) -> None:
        logger.info("Establishing AMQP connection...")
        user = quote(self.settings.amqp_user)
        password = quote(self.settings.amqp_password)
        host = self.settings.amqp_host
        url = f"amqp://{user}:{password}@{host}/"
        self.pika_connexion: aio_pika.Connection = await aio_pika.connect_robust(url)
        logger.info("AMQP connection established")

        logger.info("Opening AMQP channel...")
        self.pika_channel = await self.pika_connexion.channel(publisher_confirms=True)
        await self.pika_channel.set_qos(
            prefetch_count=self.settings.amqp_prefetch_count
        )
        logger.info("AMQP channel opened and QoS set.")

    async def fetch_publications(self, _, **extra) -> None:
        """
        Request publications for a person
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        payload = extra["payload"]
        assert isinstance(payload, dict)
        assert "person_uid" in payload, "Payload must contain 'person_uid' key"
        person_uid = payload["person_uid"]
        assert "harvesters" in payload, "Payload must contain 'harvesters' key"
        harvesters = payload["harvesters"]
        exchange = self.pika_exchanges.get(self.settings.amqp_publications_exchange_name, None)
        if not exchange:
            logger.error(f"Cannot fetch publications for person {person_uid}"
                         "AMQP exchange not declared")
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(AMQPMessagePublisher.MessageType.TASK,
                                AMQPMessagePublisher.TaskMessageSubtype.PUBLICATION_RETRIEVAL,
                                {"person_uid": person_uid, "harvesters": harvesters})

    async def dispatch_person_created(self, _, **extra) -> None:
        """
        Dispatch a person created event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        person_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.PERSON_CREATED
        await self._dispatch_person_event(event_message_subtype, person_uid)

    async def dispatch_person_updated(self, _, **extra) -> None:
        """
        Dispatch a person updated event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        person_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.PERSON_UPDATED
        await self._dispatch_person_event(event_message_subtype, person_uid)

    async def dispatch_person_unchanged(self, _, **extra) -> None:
        """
        Dispatch a person unchanged event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        person_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.PERSON_UNCHANGED
        await self._dispatch_person_event(event_message_subtype, person_uid)

    async def dispatch_person_deleted(self, _, **extra) -> None:
        """
        Dispatch a person deleted event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        person_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.PERSON_DELETED
        await self._dispatch_person_event(event_message_subtype, person_uid)

    async def _dispatch_person_event(self, event_message_subtype, person_uid):
        exchange = self.pika_exchanges.get(self.settings.amqp_graph_exchange_name, None)
        if not exchange:
            logger.error(f"Cannot dispatch {event_message_subtype} event for person {person_uid}: "
                         "AMQP exchange not declared")
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(AMQPMessagePublisher.MessageType.EVENT,
                                event_message_subtype,
                                {"person_uid": person_uid})

    async def dispatch_structure_created(self, _, **extra) -> None:
        """
        Dispatch a structure created event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        research_structure_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.STRUCTURE_CREATED
        await self._dispatch_structure_event(event_message_subtype, research_structure_uid)

    async def dispatch_structure_updated(self, _, **extra) -> None:
        """
        Dispatch a structure updated event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        research_structure_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.STRUCTURE_UPDATED
        await self._dispatch_structure_event(event_message_subtype, research_structure_uid)

    async def dispatch_structure_unchanged(self, _, **extra) -> None:
        """
        Dispatch a structure unchanged event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        research_structure_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.STRUCTURE_UNCHANGED
        await self._dispatch_structure_event(event_message_subtype, research_structure_uid)

    async def dispatch_structure_deleted(self, _, **extra) -> None:
        """
        Dispatch a structure deleted event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        research_structure_uid = extra["payload"]
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.STRUCTURE_DELETED
        await self._dispatch_structure_event(event_message_subtype, research_structure_uid)

    async def _dispatch_structure_event(self, event_message_subtype, research_structure_uid):
        exchange = self.pika_exchanges.get(self.settings.amqp_graph_exchange_name, None)
        if not exchange:
            logger.error("Cannot dispatch %s event for structure %s: "
                         "AMQP exchange not declared", event_message_subtype,
                         research_structure_uid)
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(AMQPMessagePublisher.MessageType.EVENT,
                                event_message_subtype,
                                {"research_structure_uid": research_structure_uid})

    async def dispatch_document_updated(self, _, **extra) -> None:
        """
        Dispatch a document updated event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.DOCUMENT_UPDATED
        document_uid = extra["document_uid"]
        await self._dispatch_document_event(event_message_subtype, document_uid)

    async def dispatch_document_created(self, _, **extra) -> None:
        """
        Dispatch a document created event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.DOCUMENT_CREATED
        document_uid = extra["document_uid"]
        await self._dispatch_document_event(event_message_subtype, document_uid)

    async def dispatch_document_deleted(self, _, **extra) -> None:
        """
        Dispatch a document deleted event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.DOCUMENT_DELETED
        document_uid = extra["document_uid"]
        await self._dispatch_document_event(event_message_subtype, document_uid)

    async def dispatch_document_unchanged(self, _, **extra) -> None:
        """
        Dispatch a document unchanged event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.DOCUMENT_UNCHANGED
        document_uid = extra["document_uid"]
        await self._dispatch_document_event(event_message_subtype, document_uid)

    async def _dispatch_document_event(self, event_message_subtype, document_uid):
        logger.info(
            f"Dispatching document event: {event_message_subtype}"
            f" for document {document_uid}")
        exchange = self.pika_exchanges.get(self.settings.amqp_graph_exchange_name, None)
        if not exchange:
            logger.error("Cannot dispatch %s event for document %s: "
                         "AMQP exchange not declared", document_uid)
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(AMQPMessagePublisher.MessageType.EVENT,
                                event_message_subtype,
                                {"document_uid": document_uid
                                 })

    async def dispatch_harvesting_state_event(self, _, **extra):
        """
        Dispatch a harvesting state event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.HARVESTING_STATE_EVENT
        json_payload = extra["payload"]
        exchange = self.pika_exchanges.get(self.settings.amqp_graph_exchange_name, None)
        if not exchange:
            logger.error("Graph exchange not declared. Cannot repost harvesting event.")
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(
            AMQPMessagePublisher.MessageType.EVENT,
            event_message_subtype,
            json_payload
        )

    async def dispatch_harvesting_result_event(self, _, **extra):
        """
        Dispatch a harvesting result event
        :param _: sender of message (unused)
        :param extra: extra parameters (payload of the message)
        :return: None
        """
        event_message_subtype = AMQPMessagePublisher.EventMessageSubtype.HARVESTING_RESULT_EVENT
        json_payload = extra["payload"]
        exchange = self.pika_exchanges.get(self.settings.amqp_graph_exchange_name, None)
        if not exchange:
            logger.error("Graph exchange not declared. Cannot repost harvesting result event.")
            return
        publisher = AMQPMessagePublisher(exchange)
        await publisher.publish(
            AMQPMessagePublisher.MessageType.EVENT,
            event_message_subtype,
            json_payload
        )
