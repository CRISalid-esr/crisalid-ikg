import asyncio
from unittest.mock import AsyncMock
import pytest
import aio_pika

from app.amqp.amqp_message_processor_factory import AMQPMessageProcessorFactory
from app.amqp.amqp_people_message_processor import AMQPPeopleMessageProcessor
from app.amqp.amqp_publication_message_processor import AMQPPublicationMessageProcessor
from app.config import get_app_settings
from app.settings.app_settings import AppSettings


@pytest.fixture
def mock_exchange():
    return AsyncMock(spec=aio_pika.Exchange)


@pytest.fixture
def mock_queue():
    return AsyncMock(spec=asyncio.Queue)


def test_get_publication_processor(mock_exchange, mock_queue):
    settings = get_app_settings()
    processor = AMQPMessageProcessorFactory.get_processor(
        settings.amqp_publications_topic, mock_exchange, mock_queue, settings
    )
    assert isinstance(processor, AMQPPublicationMessageProcessor)


def test_get_people_processor(mock_exchange, mock_queue):
    settings = get_app_settings()
    processor = AMQPMessageProcessorFactory.get_processor(
        settings.amqp_people_topic, mock_exchange, mock_queue, settings
    )
    assert isinstance(processor, AMQPPeopleMessageProcessor)


def test_get_processor_invalid_topic(mock_exchange, mock_queue):
    settings = get_app_settings()
    with pytest.raises(ValueError, match="No processor found for topic: invalid_topic"):
        AMQPMessageProcessorFactory.get_processor(
            "invalid_topic", mock_exchange, mock_queue, settings
        )
