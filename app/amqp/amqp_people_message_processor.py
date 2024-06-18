import json

from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor


class AMQPPeopleMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process publication messages from AMQP interface
    """

    async def _process_message(self, payload: str):
        json_payload = json.loads(payload)
        reply_expected = json_payload.get("reply", False)
        logger.debug(f"Processing message {json_payload}")
        logger.debug(f"Reply expected: {reply_expected}")
