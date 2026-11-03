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
    # 3 exchanges (graph, publications, directory), each declared with its dead-letter exchange
    assert amqp_interface.pika_channel.declare_exchange.call_count == 6
    assert [key in amqp_interface.pika_exchanges for key in
            ["people", "structures", "publications"]]


async def test_structures_topic_has_single_worker(mock_connect):  # pylint: disable=unused-argument
    """
    Structures messages must be processed sequentially (one worker) so that a child
    structure is never handled before its parents; other topics keep parallel workers.
    :param mock_connect:
    :return:
    """
    settings = get_app_settings()
    amqp_interface = AMQPInterface(settings)
    await amqp_interface.connect()
    workers = amqp_interface.message_processing_workers
    try:
        assert len(workers[settings.amqp_structures_topic]) == 1
        assert len(workers[settings.amqp_people_topic]) == settings.amqp_task_parallelism_limit
        assert len(workers[settings.amqp_publications_batch_topic]) == \
               settings.amqp_task_parallelism_limit
    finally:
        for topic_workers in workers.values():
            for worker in topic_workers:
                worker.cancel()
