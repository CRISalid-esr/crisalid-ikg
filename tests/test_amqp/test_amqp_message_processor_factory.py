import asyncio
from unittest.mock import AsyncMock

import pytest

from app.amqp.amqp_message_processor_factory import AMQPMessageProcessorFactory
from app.amqp.amqp_people_message_processor import AMQPPeopleMessageProcessor
from app.amqp.amqp_reference_message_processor import AMQReferenceMessageProcessor
from app.config import get_app_settings


@pytest.fixture(name="mock_queue")
def fixture_mock_queue() -> AsyncMock:
    """
    Mocks an asyncio.Queue object
    :return: Mock object
    """
    return AsyncMock(spec=asyncio.Queue)


def test_get_publication_processor(mock_queue) -> None:
    """
    Given the AMQPMessageProcessorFactory
    When get_processor is called with the amqp_publications_topic
    Then an AMQPPublicationMessageProcessor should be returned

    :param mock_queue: mock queue object
    :return: None
    """
    settings = get_app_settings()
    processor = AMQPMessageProcessorFactory.get_processor(
        settings.amqp_publications_topic, mock_queue
    )
    assert isinstance(processor, AMQReferenceMessageProcessor)


def test_get_people_processor(mock_queue) -> None:
    """
    Given the AMQPMessageProcessorFactory
    When get_processor is called with the amqp_people_topic
    Then an AMQPPeopleMessageProcessor should be returned
    :param mock_queue: mock queue object
    :return: None
    """
    settings = get_app_settings()
    processor = AMQPMessageProcessorFactory.get_processor(
        settings.amqp_people_topic, mock_queue
    )
    assert isinstance(processor, AMQPPeopleMessageProcessor)


def test_get_processor_invalid_topic(mock_queue) -> None:
    """
    Given the AMQPMessageProcessorFactory
    When get_processor is called with an invalid topic
    Then a ValueError should be raised
    :param mock_queue: mock queue object
    :return: None
    """
    with pytest.raises(ValueError, match="No processor found for topic: invalid_topic"):
        AMQPMessageProcessorFactory.get_processor(
            "invalid_topic", mock_queue
        )
