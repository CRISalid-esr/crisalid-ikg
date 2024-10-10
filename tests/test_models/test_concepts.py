import pytest
from pydantic import ValidationError

from app.models.concepts import Concept


def test_create_valid_concept(concept_a_json_data):
    """
    Given json data for a valid concept
    When a Pydantic model is created
    Then the values should be returned correctly
    :param person_a_pydantic_model:
    :return:
    """
    concept = Concept(**concept_a_json_data)
    assert concept.uri == concept_a_json_data["uri"]
    for pref_label in concept.pref_labels:
        assert any(pref_label.value == pref_label_data["value"]
                   and pref_label.language == pref_label_data["language"]
                   for pref_label_data in concept_a_json_data["pref_labels"])
    for alt_label in concept.alt_labels:
        assert any(alt_label.value == alt_label_data["value"]
                   and alt_label.language == alt_label_data["language"]
                   for alt_label_data in concept_a_json_data["alt_labels"])


def test_create_valid_concept_b_without_uri(concept_b_without_uri_json_data):
    """
    Given json data for a valid concept without uri
    When a Pydantic model is created
    Then the values should be returned correctly
    :param person_a_pydantic_model:
    :return:
    """
    concept = Concept(**concept_b_without_uri_json_data)
    assert concept.uri is None
    assert concept.pref_labels[0].value == concept_b_without_uri_json_data["pref_labels"][0][
        "value"]
    assert concept.pref_labels[0].language == concept_b_without_uri_json_data["pref_labels"][0][
        "language"]


async def test_create_invalid_concept_b_without_uri(invalid_concept_b_without_uri_json_data):
    """
    Given json data for an invalid concept without uri and multiple pref_labels
    When a Pydantic model is created
    Then a ValueError should be raised due to invalid data
    """
    with pytest.raises(ValidationError) as exc_info:
        Concept(**invalid_concept_b_without_uri_json_data)

    # Ensure the error message is related to having multiple pref_labels when uri is None
    assert "exactly one pref_label" in str(exc_info.value)
