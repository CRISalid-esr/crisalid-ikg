from fastapi import status
from starlette.testclient import TestClient

PERSON_API_PATH = "/api/v1/person"

RESEARCH_STRUCTURE_API_PATH = "/api/v1/organization/research-structure"


def test_create_research_structure_success(test_client: TestClient,
                                           basic_research_structure_json_data):
    """
    Given a valid person json data
    When creating a person through  REST API
    Then the person should be created successfully

    :param test_client:
    :param basic_person_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_STRUCTURE_API_PATH,
                                json=basic_research_structure_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert response.json()["structure"]["id"] == "local-U123"
    assert any(
        name["value"] == "Laboratoire toto" for name in response.json()["structure"]["names"])
    assert any(
        name["value"] == "Foobar Laboratory" for name in response.json()["structure"]["names"])
    assert any(identifier["type"] == "local" and identifier["value"] == "U123" for identifier in
               response.json()["structure"]["identifiers"])
    assert any(
        identifier["type"] == "RNSR" and identifier["value"] == "200012123S" for identifier in
        response.json()["structure"]["identifiers"])
    assert any(identifier["type"] == "ROR" and identifier["value"] == "123456" for identifier in
               response.json()["structure"]["identifiers"])


def test_create_research_structure_invalid_identifier_type(
        test_client: TestClient,
        research_structure_with_invalid_identifier_type_json_data):
    """
    Given json research structure data with invalid identifier type
    When creating a person through REST API
    Then a 422 error should be raised
    :param test_client:
    :param research_structure_with_invalid_identifier_type_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_STRUCTURE_API_PATH,
                                json=research_structure_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_research_structure_twice(test_client: TestClient,
                                         basic_research_structure_json_data):
    """
    Given a valid research structure json data
    When creating a research structure twice through REST API
    Then a 409 error should be raised

    :param test_client:
    :param basic_research_structure_json_data:
    :return:
    """
    response = test_client.post(RESEARCH_STRUCTURE_API_PATH,
                                json=basic_research_structure_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "structure" in response.json()
    assert response.json()["structure"]["id"] == "local-U123"
    response = test_client.post(RESEARCH_STRUCTURE_API_PATH,
                                json=basic_research_structure_json_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert response.json()["error"] == "Research structure with id local-U123 already exists"


def test_update_person_with_non_existent_identifier(test_client: TestClient,
                                                    basic_person_json_data):
    """
    Given a valid person json data with non existent id
    When updating a person through REST API
    Then a 404 error should be raised

    :param test_client:
    :param basic_person_json_data:
    :return:
    """
    person_with_non_existent_identifier_json_data = basic_person_json_data \
                                                    | {"id": "local-missing@univ-paris1.fr"}
    response = test_client.put(PERSON_API_PATH,
                               json=person_with_non_existent_identifier_json_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.json()
    assert response.json()["error"] == "Person with id local-missing@univ-paris1.fr does not exist"


def test_update_person_success(test_client: TestClient, basic_person_json_data):
    """
    Given a valid person json data
    When updating a person through REST API
    Then the person should be updated successfully

    :param test_client:
    :param basic_person_json_data:
    :return:
    """
    response = test_client.post(PERSON_API_PATH, json=basic_person_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    assert response.json()["person"]["id"] == "local-jdoe@univ-paris1.fr"
    assert response.json()["person"]["names"][0]["first_names"][0] == {
        "value": "John", "language": "fr"
    }
    basic_person_json_data["names"][0]["first_names"][0] = {"value": "Joe", "language": "fr"}
    response = test_client.put(PERSON_API_PATH, json=basic_person_json_data)
    assert response.status_code == status.HTTP_200_OK
    assert "person" in response.json()
    assert response.json()["person"]["names"][0]["first_names"][0] == {
        "value": "Joe", "language": "fr"
    }
