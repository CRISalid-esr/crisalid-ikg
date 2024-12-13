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
        if event_type in ["created"]:
            await self._create_source_record(source_record, person)
        elif event_type in ["updated", "unchanged"]:
            await self._update_source_record(source_record, person)

    async def _create_source_record(self, source_record, person, first_attempt=True):
        try:
            if await self.service.source_record_exists(source_record.uid):
                logger.warning(f"Source record {source_record.uid} already exists in the database")
                if first_attempt:
                    logger.warning("The system will try to update it")
                    await self._update_source_record(source_record, person, first_attempt=False)
                    return
                logger.error(f"Aborting update attempt for {source_record.uid}"
                             f" after failed create attempt", exc_info=True)
                return
            await self.service.create_source_record(source_record=source_record,
                                                    harvested_for=person)
        except ReferenceOwnerNotFoundError as e:
            logger.error(
                f"Reference owner {person} not found while trying to create source record"
                f"{source_record} : {e}")
            raise e
        except ConflictError as e:
            logger.warning(
                f"Identifier conflict while trying to create source record {source_record} : {e}")
            logger.error(f"{source_record.uid} already exists in the database", exc_info=True)
        except DatabaseError as e:
            logger.error(
                f"Database error while trying to create source record {source_record} : {e}")
            raise e

    async def _update_source_record(self, source_record, person, first_attempt=True):
        try:
            if await self.service.source_record_exists(source_record.uid):
                await self.service.update_source_record(source_record=source_record,
                                                        harvested_for=person)
            else:
                logger.warning(f"Source record {source_record.uid} does not exist in the database")
                if first_attempt:
                    logger.warning("The system will try to create it")
                    await self._create_source_record(source_record, person, first_attempt=False)
                else:
                    logger.error(f"Aborting create attempt for {source_record.uid}"
                             f" after failed update attempt", exc_info=True)
        except ReferenceOwnerNotFoundError as e:
            logger.error(
                f"Reference owner {person} not found while trying to update source record"
                f" {source_record} : {e}")
            raise e
        except ConflictError as e:
            logger.error(
                f"Identifier conflict while trying to update source record {source_record} : {e}")
            raise e
        except DatabaseError as e:
            logger.error(
                f"Database error while trying to update source record {source_record} : {e}")
            raise e
