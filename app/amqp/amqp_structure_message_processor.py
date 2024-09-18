import json

from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.models.research_structures import ResearchStructure
from app.services.organizations.research_structure_service import ResearchStructureService


class AMQPStructureMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about structures from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = ResearchStructureService()

    async def _process_message(self, key: str, payload: str):
        json_payload = json.loads(payload)
        logger.debug(f"Processing message {json_payload}")
        event_data = json_payload["structures_event"]
        event_type = event_data["type"]
        structure_data = event_data["data"]
        try:
            structure = ResearchStructure(**structure_data)
        except ValidationError as e:
            logger.error(f"Error processing structure data {structure_data} : {e}")
            raise e
        if event_type == "created":
            await self._create_structure(structure)
        elif event_type == "updated":
            await self._update_structure(structure)
        elif event_type == "unchanged":
            logger.debug(f"Structure {structure} unchanged")
            await self._create_or_update_structure(structure)

    async def _create_structure(self, structure):
        try:
            await self.service.create_structure(structure)
        except ConflictError as e:
            logger.error(f"Identifier conflict while trying to create structure {structure} : {e}")
            logger.error("Will try to update the structure instead")
            await self._update_structure(structure)

    async def _update_structure(self, structure):
        try:
            await self.service.update_structure(structure)
        except NotFoundError as e:
            logger.error(f"Structure not found while trying to update structure {structure} : {e}")
            logger.error("Will try to create the structure instead")
            await self._create_structure(structure)
        except ConflictError as e:
            logger.error(f"Identifier conflict while trying to update structure {structure} : {e}")

    async def _create_or_update_structure(self, structure):
        await self.service.create_or_update_structure(structure)
