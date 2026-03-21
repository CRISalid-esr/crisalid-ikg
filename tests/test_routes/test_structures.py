from fastapi import status
from starlette.testclient import TestClient

PERSON_API_PATH = "/api/v1/person"

RESEARCH_UNIT_API_PATH = "/api/v1/organization/research-unit"


def test_create_research_unit_success(test_client: TestClient,
                                           research_unit_a_json_data):
    """
    Given a valid person json data
    When creating a person through  REST API
    Then the person should be created successfully

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_UNIT_API_PATH,
                                json=research_unit_a_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert response.json()["structure"]["uid"] == "local-U123"
    assert any(
        name["value"] == "Laboratoire toto" for name in response.json()["structure"]["names"])
    assert any(
        name["value"] == "Foobar Laboratory" for name in response.json()["structure"]["names"])
    assert any(identifier["type"] == "local" and identifier["value"] == "U123" for identifier in
               response.json()["structure"]["identifiers"])
    assert any(
        identifier["type"] == "nns" and identifier["value"] == "200012123S" for identifier in
        response.json()["structure"]["identifiers"])
    assert any(identifier["type"] == "ror" and identifier["value"] == "123456" for identifier in
               response.json()["structure"]["identifiers"])


def test_create_research_unit_invalid_identifier_type(
        test_client: TestClient,
        research_unit_a_with_invalid_identifier_type_json_data):
    """
    Given json research structure data with invalid identifier type
    When creating a structure through REST API
    Then a 422 error should be raised
    :param test_client:
    :param research_unit_a_with_invalid_identifier_type_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_UNIT_API_PATH,
                                json=research_unit_a_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_research_unit_invalid_identifier_type(
        test_client: TestClient,
        research_unit_a_with_invalid_identifier_type_json_data):
    """
    Given json research structure data with invalid identifier type
    When updating a structure through REST API
    Then a 422 error should be raised
    :param test_client:
    :param research_unit_a_with_invalid_identifier_type_json_data:
    :return:
    """
    response = test_client.put(RESEARCH_UNIT_API_PATH,
                               json=research_unit_a_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_research_unit_twice(test_client: TestClient,
                                         research_unit_a_json_data):
    """
    Given a valid research structure json data
    When creating a research structure twice through REST API
    Then a 409 error should be raised

    :param test_client:
    :param research_unit_a_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_UNIT_API_PATH,
                                json=research_unit_a_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert response.json()["structure"]["uid"] == "local-U123"
    response = test_client.post(RESEARCH_UNIT_API_PATH,
                                json=research_unit_a_json_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert response.json()["error"] == "Research structure with uid local-U123 already exists"


def test_create_research_unit_b_without_name(
        test_client: TestClient, research_unit_b_without_name_json_data
):
    """
    Given a valid person json data
    When creating a person through  REST API
    Then the person should be created successfully

    :param test_client:
    :param research_unit_b_without_name_json_data:
    :return:
    """
    response = test_client.post(
        RESEARCH_UNIT_API_PATH, json=research_unit_b_without_name_json_data
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert len(response.json()["structure"]["names"]) == 0
    assert len(response.json()["structure"]["identifiers"]) == 3
    assert response.json()["structure"]["uid"] == "local-U153"
