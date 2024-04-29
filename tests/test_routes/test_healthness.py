"""Test the references API."""

import pytest
from fastapi.testclient import TestClient


def test_healthness_route_answers(test_client: TestClient):
    """Test the healthness route."""
    response = test_client.get("/health")
    assert response.status_code == 200
