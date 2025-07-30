# file: app/amqp/amqp_user_actions_message_processor.py

from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.signals import harvesting_state_event_received, harvesting_result_event_received


class AMQPHarvestingEventsMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about harvesting events from AMQP interface
    The worker listens to the `amqp_harvesting_events_topic` and reposts the messages
    to the `graph` exchange for downstream applications to consume.
    """

    async def _process_message(self, key: str, payload: str):
        json_payload = await self._read_message_json(payload)
        logger.debug(f"Reposting harvesting event message for downstream apps: {json_payload}")
        if "harvester" in json_payload and "state" in json_payload:
            await harvesting_state_event_received.send_async(self, payload=json_payload)
        elif "reference_event" in json_payload:
            await harvesting_result_event_received.send_async(self, payload=json_payload)
        else:
            logger.debug(f"Message will not be processed : {json_payload}.")
