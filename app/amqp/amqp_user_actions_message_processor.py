# file: app/amqp/amqp_user_actions_message_processor.py

from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.models.change import Change
from app.services.changes.change_service import ChangeService


class AMQPUserActionsMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about user actions from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_service = ChangeService()

    async def _process_message(self, key: str, payload: str):
        json_payload = await self._read_message_json(payload)
        logger.debug(f"Processing user action message: {json_payload}")

        self._check_keys(json_payload, {
            "id": None,
            "actionType": None,
            "parameters": None,
            "path": None,
            "personUid": None,
            "targetType": None,
            "targetUid": None,
            "timestamp": None,
            "application": None,  # make sure 'clientApp' is present to build the UID
        })

        try:
            change = Change.model_validate(json_payload)
        except ValidationError as e:
            raise ValueError(f"Failed to build Change object: {e}") from e
        # exceptions are handled in the base class
        await self.change_service.create_and_apply_change(change)
