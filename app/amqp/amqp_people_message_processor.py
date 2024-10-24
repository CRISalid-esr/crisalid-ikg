import json

from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.errors.conflict_error import ConflictError
from app.errors.not_found_error import NotFoundError
from app.models.people import Person
from app.services.people.people_service import PeopleService


class AMQPPeopleMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about people from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = PeopleService()

    async def _process_message(self, key: str, payload: str):
        json_payload = json.loads(payload)
        logger.debug(f"Processing message {json_payload}")
        event_data = json_payload["people_event"]
        event_type = event_data["type"]
        person_data = event_data["data"]
        try:
            person = Person(**person_data)
        except ValueError as e:
            logger.error(f"Error processing person data {person_data} : {e}")
            raise e
        if event_type == "created":
            await self._create_person(person)
        elif event_type == "updated":
            await self._update_person(person)
        elif event_type == "unchanged":
            logger.debug(f"Person {person} unchanged")
            await self._create_or_update_person(person)

    async def _create_person(self, person: Person, retry=False):
        try:
            await self.service.create_person(person)
        except ConflictError as e:
            logger.error(f"Identifier conflict while trying to create person {person} : {e}")
            if not retry:
                logger.error("Will try to update the person instead")
                await self._update_person(person, retry=True)

    async def _update_person(self, person: Person, retry=False):
        try:
            await self.service.update_person(person)
        except ConflictError as e:
            logger.error(f"Identifier conflict while trying to update person {person} : {e}")
        except NotFoundError as e:
            logger.error(f"Error while trying to update person {person} : {e}")
            if not retry:
                logger.error("Will try to create the person instead")
                await self._create_person(person, retry=True)

    async def _create_or_update_person(self, person: Person):
        try:
            await self.service.create_or_update_person(person)
        except ConflictError as e:
            logger.error("Identifier conflict while trying "
                         f"to create or update person {person} : {e}")
