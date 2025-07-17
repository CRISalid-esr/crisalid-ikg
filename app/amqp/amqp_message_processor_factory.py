import asyncio

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.amqp.amqp_people_message_processor import AMQPPeopleMessageProcessor
from app.amqp.amqp_reference_message_processor import AMQReferenceMessageProcessor
from app.amqp.amqp_structure_message_processor import AMQPStructureMessageProcessor
from app.amqp.amqp_user_actions_message_processor import AMQPUserActionsMessageProcessor
from app.config import get_app_settings


class AMQPMessageProcessorFactory:
    """
    Factory to create AMQP message processor adapted to the message topic
    """

    @staticmethod
    def get_processor(
            topic: str,
            tasks_queue: asyncio.Queue,
    ) -> AMQPMessageProcessor:
        """
        Get the appropriate processor for the given topic
        :param topic:
        :param tasks_queue:
        :param settings:
        :return:
        """
        settings = get_app_settings()
        if topic == settings.amqp_publications_topic:
            return AMQReferenceMessageProcessor(tasks_queue, settings)
        if topic == settings.amqp_people_topic:
            return AMQPPeopleMessageProcessor(tasks_queue, settings)
        if topic == settings.amqp_structures_topic:
            return AMQPStructureMessageProcessor(tasks_queue, settings)
        if topic == settings.amqp_user_actions_topic:
            return AMQPUserActionsMessageProcessor(tasks_queue, settings)
        raise ValueError(f"No processor found for topic: {topic}")
