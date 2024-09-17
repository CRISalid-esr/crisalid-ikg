from unittest.mock import AsyncMock

from app.amqp.amqp_interface import AMQPInterface
from app.config import get_app_settings


async def test_amqp_connect(mock_connect):
    """
    Test AMQP interface initialization.
    :param mock_connect:
    :return:
    """
    settings = get_app_settings()
    amqp_interface = AMQPInterface(settings)
    await amqp_interface.connect()
    assert isinstance(amqp_interface.pika_channel.set_qos, AsyncMock)
    assert isinstance(amqp_interface.pika_channel.declare_exchange, AsyncMock)
    assert mock_connect.call_count == 1
    assert mock_connect.call_args[0][
               0] == "amqp://rabbitmq_test_user:rabbitmq_test_password@rabbitmq_test_host/"
    assert amqp_interface.pika_channel.set_qos.called
    assert amqp_interface.pika_channel.declare_exchange.call_count == 3
    assert [key in amqp_interface.pika_exchanges for key in
            ["people", "structures", "publications"]]
