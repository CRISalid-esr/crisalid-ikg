import asyncio
from os import environ

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

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
