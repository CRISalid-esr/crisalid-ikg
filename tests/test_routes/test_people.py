# test_people.py
import pytest
from fastapi import status
from starlette.testclient import TestClient


def test_create_person_success(test_client: TestClient, basic_person_json_data):
    response = test_client.post("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()


def test_create_person_invalid_data(test_client: TestClient, person_with_invalid_identifier_type_json_data):
    response = test_client.post("/api/v1/person", json=person_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
