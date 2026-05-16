from fastapi import status
from starlette.testclient import TestClient

PERSON_API_PATH = "/api/v1/person"

RESEARCH_UNIT_API_PATH = "/api/v1/organization/research-unit"


def test_create_research_unit_success(test_client: TestClient,
                                      research_unit_center_json_data):
    response = test_client.post(RESEARCH_UNIT_API_PATH, json=research_unit_center_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert response.json()["structure"]["uid"] == "local-CENTER-001"
    assert any(
        ll["value"] == "Example Research Center"
        for ll in response.json()["structure"]["long_labels"]
    )
    assert any(
        identifier["type"] == "local" and identifier["value"] == "CENTER-001"
        for identifier in response.json()["structure"]["identifiers"]
    )


def test_create_research_unit_invalid_identifier_type(
        test_client: TestClient,
        research_unit_a_with_invalid_identifier_type_json_data):
    response = test_client.post(RESEARCH_UNIT_API_PATH,
                                json=research_unit_a_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_research_unit_invalid_identifier_type(
        test_client: TestClient,
        research_unit_a_with_invalid_identifier_type_json_data):
    response = test_client.put(RESEARCH_UNIT_API_PATH,
                               json=research_unit_a_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_research_unit_twice(test_client: TestClient,
                                    research_unit_center_json_data):
    response = test_client.post(RESEARCH_UNIT_API_PATH, json=research_unit_center_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["structure"]["uid"] == "local-CENTER-001"
    response = test_client.post(RESEARCH_UNIT_API_PATH, json=research_unit_center_json_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert "local-CENTER-001" in response.json()["error"]


def test_create_research_unit_without_labels(
        test_client: TestClient, research_unit_without_labels_json_data
):
    response = test_client.post(
        RESEARCH_UNIT_API_PATH, json=research_unit_without_labels_json_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert len(response.json()["structure"]["long_labels"]) == 0
    assert len(response.json()["structure"]["identifiers"]) == 3
    assert response.json()["structure"]["uid"] == "local-U153"
