import asyncio
from os import environ

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from tests.fixtures.common import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import
from tests.fixtures.people_fixtures import *  # pylint: disable=unused-import, wildcard-import, unused-wildcard-import

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
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    global_dao = factory.get_dao()
    await global_dao.reset_all()
    yield
    await global_dao.reset_all()