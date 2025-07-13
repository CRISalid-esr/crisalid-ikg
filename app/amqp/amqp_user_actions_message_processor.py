from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.services.documents.document_service import DocumentService


class AMQPUserActionsMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about user actions from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = DocumentService()

    async def _process_message(self, key: str, payload: str):
        json_payload = await self._read_message_json(payload)
        logger.debug(f"Processing message {json_payload}")
        self._check_keys(json_payload, {
            "id": None,
            "action": None,
            "parameters": None,
            "path": None,
            "personUid": None,
            "targetType": None,
            "targetUid": None,
            "timestamp": None,

        })
        logger.debug(f"Processing message {json_payload}")
        raise ValueError("Impossible to process user action message, ")
