from os import environ
from unittest.mock import AsyncMock

from _pytest.logging import LogCaptureFixture
from aio_pika import Exchange, Connection, Channel
from fastapi import FastAPI
from loguru import logger
from starlette.testclient import TestClient
from yarl import URL

from app.crisalid_ikg import CrisalidIKG
from tests.fixtures.common import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.people_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.organization_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.source_record_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.source_record_id_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.document_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.concepts_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.source_journal_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.source_organizations_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.institution_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.issn_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import

environ["APP_ENV"] = "TEST"


@pytest.fixture(name="test_app")
def app() -> FastAPI:
    """Provide app as fixture"""
    # pylint: disable=import-outside-toplevel

    return CrisalidIKG()


@pytest.fixture(name="test_client")
def fixture_test_client(test_app: FastAPI) -> TestClient:
    """Provide test client as fixture"""
    return TestClient(test_app)


@pytest.fixture(scope="function", autouse=True)
async def reset_graph():
    """Reset the graph database before and after each test"""
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    global_dao = factory.get_dao()
    await global_dao.reset_all()
    yield
    await global_dao.reset_all()
    setup = factory.get_setup()
    await setup.run()


@pytest.fixture(autouse=True)
def caplog(caplog: LogCaptureFixture):  # pylint: disable=redefined-outer-name
    """
    Make pytest work with loguru. See:
    https://loguru.readthedocs.io/en/stable/resources/migration.html#making-things-work-with-pytest-and-caplog
    :param caplog: pytest fixture
    :return: loguru compatible caplog
    """
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,
    )
    yield caplog
    try:
        logger.remove(handler_id)
    except ValueError:
        pass


@pytest.fixture(name="mocked_exchange")
def mock_exchange():
    """
    Mocked RabbitMQ exchange to control publish calls.
    """
    mocked_exchange = Exchange(
        Channel(Connection(URL("http://foobar"))), "tests_amqp_queue"
    )
    mocked_exchange.publish = AsyncMock()
    return mocked_exchange
