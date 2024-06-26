from fastapi import status
from starlette.testclient import TestClient


def test_create_person_success(test_client: TestClient, basic_person_json_data):
    """
    Given a valid person json data
    When creating a person through  REST API
    Then the person should be created successfully

    :param test_client:
    :param basic_person_json_data:
    :return:
    """
    response = test_client.post("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    # id of the person should be generated
    assert response.json()["person"]["id"] == "local-jdoe@univ-paris1.fr"


def test_create_person_invalid_data(test_client: TestClient,
                                    person_with_invalid_identifier_type_json_data):
    """
    Given json person data with invalid identifier type
    When creating a person through REST API
    Then a 422 error should be raised

    :param test_client:
    :param person_with_invalid_identifier_type_json_data:
    :return:
    """
    response = test_client.post("/api/v1/person",
                                json=person_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_person_twice(test_client: TestClient, basic_person_json_data):
    """
    Given a valid person json data
    When creating a person twice through REST API
    Then a 409 error should be raised

    :param test_client:
    :param basic_person_json_data:
    :return:
    """
    response = test_client.post("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    assert response.json()["person"]["id"] == "local-jdoe@univ-paris1.fr"
    response = test_client.post("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert response.json()["error"] == "Person with id local-jdoe@univ-paris1.fr already exists"


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
    response = test_client.put("/api/v1/person",
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
    response = test_client.post("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    assert response.json()["person"]["id"] == "local-jdoe@univ-paris1.fr"
    assert response.json()["person"]["names"][0]["first_names"][0] == "John"
    basic_person_json_data["names"][0]["first_names"][0] = "Joe"
    response = test_client.put("/api/v1/person", json=basic_person_json_data)
    assert response.status_code == status.HTTP_200_OK
    assert "person" in response.json()
    assert response.json()["person"]["names"][0]["first_names"][0] == "Joe"
