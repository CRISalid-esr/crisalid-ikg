from unittest import mock

import aio_pika
import pytest


@pytest.fixture(name="mock_connect")
def mock_connect():
    """
    Mocked RabbitMQ connection to control connect calls.
    """
    with mock.patch("aio_pika.connect_robust") as connect:
        yield connect


@pytest.fixture(name="mocked_message")
def mock_message():
    """
    Retrieval service mock to detect run method calls.
    """
    with mock.patch.object(aio_pika, "Message") as exch:
        yield exch
