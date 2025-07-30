from unittest.mock import AsyncMock, patch

import aio_pika
import pytest


@pytest.fixture(name="mocked_publish")
def mocked_publish():
    """
    Mocked RabbitMQ publisher to control publish calls.
    """
    with patch("app.amqp.amqp_interface.AMQPMessagePublisher.publish",
                    new_callable=AsyncMock) as publish:
        yield publish


@pytest.fixture(name="mock_connect")
def mock_connect():
    """
    Mocked RabbitMQ connection to control connect calls.
    """
    with patch("aio_pika.connect_robust") as connect:
        yield connect


@pytest.fixture(name="mocked_message")
def mock_message():
    """
    Retrieval service mock to detect run method calls.
    """
    with patch.object(aio_pika, "Message") as exch:
        yield exch
