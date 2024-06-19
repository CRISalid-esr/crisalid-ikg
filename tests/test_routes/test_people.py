# test_people.py
import pytest
from fastapi import status
from starlette.testclient import TestClient


@pytest.fixture
def valid_person_data():
    return {
        "names": [
            {
                "first_names": [
                    "John"
                ],
                "family_names": [
                    "Doe"
                ],
                "other_names": [
                    "Johnny"
                ]
            }
        ],
        "identifiers": [
            {
                "type": "ORCID",
                "value": "0000-0001-2345-6789"
            },
            {
                "type": "local",
                "value": "jdoe@univ-paris1.fr"
            }
        ]
    }


def test_create_person_success(test_client: TestClient, valid_person_data):
    response = test_client.post("/api/v1/person", json=valid_person_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()


def test_create_person_invalid_data(test_client: TestClient):
    invalid_person_data = {
    }
    response = test_client.post("/api/v1/person", json=invalid_person_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
