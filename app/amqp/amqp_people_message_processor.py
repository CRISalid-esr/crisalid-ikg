import json

from loguru import logger

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.people_dao import PeopleDAO
from app.models.people import Person


class AMQPPeopleMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process publication messages from AMQP interface
    """

    async def _process_message(self, payload: str):
        json_payload = json.loads(payload)
        logger.debug(f"Processing message {json_payload}")
        settings = get_app_settings()
        factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
        person_data = json_payload["person"]
        person = Person(**person_data)
        dao: PeopleDAO = factory.get_dao(Person)
        try:
            await dao.create_or_update(person)
        except Exception as e:
            logger.error(f"Error processing message {json_payload}: {e}")
            raise e
