from os import environ

from fastapi import FastAPI
from starlette.testclient import TestClient

from tests.fixtures.common import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.people_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.organization_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.source_record_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.concepts_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import

environ["APP_ENV"] = "TEST"


@pytest.fixture(name="test_app")
def app() -> FastAPI:
    """Provide app as fixture"""
    # pylint: disable=import-outside-toplevel
    from app.main import CrisalidIKG  # local import for testing purpose

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
