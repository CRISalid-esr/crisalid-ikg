from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.errors.conflict_error import ConflictError
from app.errors.database_error import DatabaseError
from app.errors.reference_owner_not_found_error import ReferenceOwnerNotFoundError
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


class AMQReferenceMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process publication messages from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = SourceRecordService()

    async def _process_message(self, key: str, payload: str):
        json_payload = await self._read_message_json(payload)
        logger.info(f"Processing message {json_payload}")
        self._check_keys(json_payload, {
            "reference_event": ["type"],
            "entity": []
        })
        event_data = json_payload["reference_event"]
        person_data = json_payload["entity"]
        event_type = event_data["type"]
        reference_data = event_data["reference"]
        try:
            person = Person(**person_data)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error processing person data associated with incoming reference"
                         f" {person_data} : {e}")
            raise e
        try:
            source_record = SourceRecord(**reference_data)
        except (ValueError, AttributeError) as e:
            logger.error(f"Error processing source record data {reference_data} : {e}")
            raise e
        if event_type in ["created", "unchanged"]:  # TODO temporary use create for unchanged
            await self._create_source_record(source_record, person)

    async def _create_source_record(self, source_record, person):
        try:
            await self.service.create_source_record(source_record=source_record,
                                                    harvested_for=person)
        except ReferenceOwnerNotFoundError as e:
            logger.error(
                f"Reference owner {person} not found while trying to create source record"
                f" not found while trying to create source record {source_record} : {e}")
            raise e
        except ConflictError as e:
            logger.error(
                f"Identifier conflict while trying to create source record {source_record} : {e}")
            logger.error("Will try to update the source record instead")
            raise e
        except DatabaseError as e:
            logger.error(
                f"Database error while trying to create source record {source_record} : {e}")
            raise e
