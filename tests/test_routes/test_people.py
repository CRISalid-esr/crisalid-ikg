# test_people.py

from fastapi import status
from starlette.testclient import TestClient


def test_create_person_success(test_client: TestClient):
    person_data = {
        "first_names": ["John", "F."],
        "last_names": ["Doe"],
        "alternative_names": ["Johnny"],
        "identifiers": [
            {
                "type": "ORCID",
                "value": "0000-0002-1825-0097"
            },
            {
                "type": "ScopusEID",
                "value": "2-s2.0-84981234567"
            }
        ]
    }

    response = test_client.post("/api/v1/person", json=person_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()


def test_create_person_invalid_data(test_client: TestClient):
    invalid_person_data = {
    }
    response = test_client.post("/api/v1/person", json=invalid_person_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
