import asyncio
import json
from abc import ABC, abstractmethod
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from loguru import logger

from app.errors.database_error import DatabaseError
from app.errors.message_error import UnreadableMessageError
from app.settings.app_settings import AppSettings


class AMQPMessageProcessor(ABC):
    """
    Workers to process messages from AMQP interface
    """

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

        while True:
            message: IncomingMessage | None = await self.tasks_queue.get()
            start_time = datetime.now()
            requeue = False
            async with message.process(ignore_processed=True):
                payload = message.body
                key = message.routing_key
                try:
                    await self._process_message(key, payload)
                    await message.ack()
                    self.tasks_queue.task_done()
                except ValueError as error:
                    logger.error(
                        f"Invalid message received by {worker_id} : {error}",
                        exc_info=True
                    )
                except DatabaseError as database_error:
                    logger.error(
                        f"Database error during {worker_id} "
                        f"message processing : {database_error}",
                        exc_info=True
                    )
                    requeue = True
                except KeyboardInterrupt as keyboard_interrupt:
                    logger.warning(f"Amqp connect worker {worker_id} has been cancelled")
                    await message.nack(requeue=True)
                    raise keyboard_interrupt
                except Exception as exception:  # pylint: disable=broad-exception-caught
                    logger.error(
                        f"Unexpected exception during {worker_id} message processing: {exception}",
                        exc_info=True
                    )
                finally:
                    if not message.processed:
                        await message.nack(requeue=requeue)
                        self.tasks_queue.task_done()
                    end_time = datetime.now()
                    logger.warning(
                        f"Performance : Message  processed by {worker_id} "
                        f"in {end_time - start_time} for payload {payload}"
                    )

    @abstractmethod
    async def _process_message(self, key: str, payload: str) -> None:
        """
        Abstract method to process message
        :param payload: message payload
        :return: None
        """

    @staticmethod
    async def _read_message_json(payload):
        try:
            json_payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as e:
            logger.error(f"Error decoding incoming message payload {payload} : {e}")
            raise UnreadableMessageError from e
        return json_payload

    @staticmethod
    def _check_keys(payload, required_keys):
        """
        Check if all required keys and subkeys exist in the payload dictionary.

        :param payload: dict - The JSON payload to check.
        :param required_keys: dict - A dictionary specifying required keys and their subkeys.
        e.g. {"key1": ["subkey1", "subkey2"], "key2": None}
        :raises UnreadableMessageError: if any required key or subkey is missing.
        """
        for key, subkeys in required_keys.items():
            if key not in payload:
                raise UnreadableMessageError(f"Missing key '{key}' in payload.")

            if isinstance(subkeys, list):  # Check for subkeys
                if not isinstance(payload[key], dict):
                    raise UnreadableMessageError(f"Expected '{key}' to be a dictionary.")
                for subkey in subkeys:
                    if subkey not in payload[key]:
                        raise UnreadableMessageError(f"Missing subkey '{subkey}' in '{key}'.")
