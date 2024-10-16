from fastapi import status
from starlette.testclient import TestClient

API_PERSON_PATH = "/api/v1/person"


def test_create_person_success(test_client: TestClient, person_a_json_data):
    """
    Given a valid person json data
    When creating a person through  REST API
    Then the person should be created successfully

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    response = test_client.post(API_PERSON_PATH, json=person_a_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    # uid of the person should be generated
    assert response.json()["person"]["uid"] == "local-jdoe@univ-domain.edu"


def test_create_person_invalid_data(test_client: TestClient,
                                    person_a_with_invalid_identifier_type_json_data):
    """
    Given json person data with invalid identifier type
    When creating a person through REST API
    Then a 422 error should be raised

    :param test_client:
    :param person_a_with_invalid_identifier_type_json_data:
    :return:
    """
    response = test_client.post(API_PERSON_PATH,
                                json=person_a_with_invalid_identifier_type_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_person_twice(test_client: TestClient, person_a_json_data):
    """
    Given a valid person json data
    When creating a person twice through REST API
    Then a 409 error should be raised

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    response = test_client.post(API_PERSON_PATH, json=person_a_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    assert response.json()["person"]["uid"] == "local-jdoe@univ-domain.edu"
    response = test_client.post(API_PERSON_PATH, json=person_a_json_data)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert response.json()["error"] == "Person with uid local-jdoe@univ-domain.edu already exists"


def test_update_person_with_non_existent_identifier(test_client: TestClient,
                                                    person_a_json_data):
    """
    Given a valid person json data with non existent uid
    When updating a person through REST API
    Then a 404 error should be raised

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    person_with_non_existent_identifier_json_data = person_a_json_data \
                                                    | {"uid": "local-missing@univ-domain.edu"}
    response = test_client.put(API_PERSON_PATH,
                               json=person_with_non_existent_identifier_json_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in response.json()
    assert response.json()[
               "error"] == "Person with uid local-missing@univ-domain.edu does not exist"


def test_update_person_success(test_client: TestClient, person_a_json_data):
    """
    Given a valid person json data
    When updating a person through REST API
    Then the person should be updated successfully

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    response = test_client.post(API_PERSON_PATH, json=person_a_json_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "person" in response.json()
    assert response.json()["person"]["uid"] == "local-jdoe@univ-domain.edu"
    assert response.json()["person"]["names"][0]["first_names"][0] == {
        "value": "John", "language": "fr"
    }
    person_a_json_data["names"][0]["first_names"][0] = {"value": "Joe", "language": "fr"}
    response = test_client.put(API_PERSON_PATH, json=person_a_json_data)
    assert response.status_code == status.HTTP_200_OK
    assert "person" in response.json()
    assert response.json()["person"]["names"][0]["first_names"][0] == {
        "value": "Joe", "language": "fr"
    }


def test_update_person_with_non_authorized_identifier(test_client: TestClient,
                                                      person_a_json_data):
    """
    Given a person json data with an invalid identifier type
    When updating a person through REST API
    Then a 422 error should be raised

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    person_with_non_authorized_identifier_json_data = person_a_json_data \
                                                      | {"identifiers": person_a_json_data.get(
        "identifiers", []) + [{
        "type": "invalide",
        "value": "blabla"
    }]}
    response = test_client.put(API_PERSON_PATH,
                               json=person_with_non_authorized_identifier_json_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
