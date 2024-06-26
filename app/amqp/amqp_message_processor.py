import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from loguru import logger

from app.settings.app_settings import AppSettings

DEFAULT_RESULT_TIMEOUT = 600


class AMQPMessageProcessor(ABC):
    """
    Workers to process messages from AMQP interface
    """

    MAX_EXPECTED_RESULTS = 10000

    def __init__(
            self,
            exchange: aio_pika.Exchange,
            tasks_queue: asyncio.Queue,
            settings: AppSettings,
    ):
        self.exchange = exchange
        self.tasks_queue = tasks_queue
        self.settings = settings

    async def wait_for_message(self, worker_id: int) -> None:
        """
        Messages awaiting method for async processing
        :param worker_id: queue worker identifier
        :return: None
        """
        message: IncomingMessage | None = None
        try:
            while True:
                message = await self.tasks_queue.get()
                start_time = datetime.now()
                async with message.process(ignore_processed=True):
                    payload = message.body
                    key = message.routing_key
                    await self._process_message(key, payload)
                    await message.ack()
                    self.tasks_queue.task_done()
                    end_time = datetime.now()
                    logger.warning(
                        f"Performance : Message  processed by {worker_id} "
                        f"in {end_time - start_time} for payload {payload}"
                    )
        except KeyboardInterrupt:
            await message.nack(requeue=True)
            logger.warning(f"Amqp connect worker {worker_id} has been cancelled")
        except Exception as exception:
            await message.nack(requeue=True)
            logger.error(
                f"Exception during {worker_id} message processing : {exception}"
            )
            raise exception

    @abstractmethod
    async def _process_message(self, key:str, payload: str) -> None:
        """
        Abstract method to process message
        :param payload: message payload
        :return: None
        """
