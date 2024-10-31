from fastapi import status
from starlette.testclient import TestClient

API_SOURCE_RECORDS_PATH = "/api/v1/source_records"


def test_create_source_records_success(
        test_client: TestClient,
        persisted_person_a_pydantic_model,  # pylint: disable=unused-argument
        idref_record_with_person_a_as_contributor_json_data,
        person_a_json_data
):
    """
    Given a valid source record json data and json data from an existing person_a_pydantic_model
    When creating a source record through  REST API
    Then the source record should be created successfully

    :param test_client:
    :param idref_record_with_person_a_as_contributor_json_data:
    :param person_a_json_data:
    :return:
    """
    model = {
        "source_record": idref_record_with_person_a_as_contributor_json_data,
        "person": person_a_json_data
    }
    response = test_client.post(API_SOURCE_RECORDS_PATH, json=model)
    assert response.status_code == status.HTTP_201_CREATED
    assert "source_record" in response.json()
    assert response.json()["source_record"]["source_identifier"] == \
           idref_record_with_person_a_as_contributor_json_data["source_identifier"]


def test_create_source_records_for_unknown_person(test_client: TestClient,
                                                   idref_record_with_person_a_as_contributor_json_data,
                                                   person_a_json_data
                                                   ):
    """
    Given a valid source record data, with an unknown person a json_data,
    When creating a source record through REST API
    Then a 422 error should be raised

    :param test_client:
    :param idref_record_with_person_a_as_contributor_json_data:
    :param person_a_json_data:
    :return:
    """
    model = {
        "source_record": idref_record_with_person_a_as_contributor_json_data,
        "person": person_a_json_data
    }
    response = test_client.post(API_SOURCE_RECORDS_PATH,
                                json=model)
    # ReferenceOwnerNotFoundError is raised by the model, and is caught by the router
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_source_record_with_invalid_record_data(
        test_client: TestClient,
        persisted_person_a_pydantic_model,  # pylint: disable=unused-argument
        idref_record_with_person_a_as_contributor_json_data,
        person_a_json_data
):
    """
    Given json source record data with an empty mandatory field
    When creating a person through REST API
    Then a 422 error should be raised

    :param test_client:
    :param idref_record_with_person_a_as_contributor_json_data:
    :param person_a_json_data:
    :return:
    """
    idref_record_with_person_a_as_contributor_json_data["titles"] = []
    model = {
        "source_record": idref_record_with_person_a_as_contributor_json_data,
        "person": person_a_json_data
    }

    response = test_client.post(API_SOURCE_RECORDS_PATH,
                                json=model)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_source_record_with_missing_record_data(
        test_client: TestClient,
        persisted_person_a_pydantic_model,  # pylint: disable=unused-argument
        person_a_json_data
):
    """
    Given a post to the source record route, for a known person, but with no record data
    When creating a source_record through REST API
    Then a 422 error should be raised

    :param test_client:
    :param person_a_json_data:
    :return:
    """
    model = {
        "source_record": {},
        "person": person_a_json_data
    }

    response = test_client.post(API_SOURCE_RECORDS_PATH,
                                json=model)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_source_record_twice(
        test_client: TestClient,
        persisted_person_a_pydantic_model,  # pylint: disable=unused-argument
        idref_record_with_person_a_as_contributor_json_data,
        person_a_json_data):
    """
    Given a valid source record json data and json data from an existing person_a_pydantic_model
    When creating a source record twice through REST API
    Then a 409 error should be raised

    :param test_client:
    :param idref_record_with_person_a_as_contributor_json_data:
    :param person_a_json_data:
    :return:
    """
    model = {
        "source_record": idref_record_with_person_a_as_contributor_json_data,
        "person": person_a_json_data
    }

    response = test_client.post(API_SOURCE_RECORDS_PATH, json=model)
    assert response.status_code == status.HTTP_201_CREATED
    assert "source_record" in response.json()
    assert response.json()["source_record"]["source_identifier"] == \
           idref_record_with_person_a_as_contributor_json_data["source_identifier"]
    response = test_client.post(API_SOURCE_RECORDS_PATH, json=model)
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "error" in response.json()
    assert (response.json()["error"] ==
            "Source record with uid Idref-http://www.idref.fr/247889784/id already exists")
