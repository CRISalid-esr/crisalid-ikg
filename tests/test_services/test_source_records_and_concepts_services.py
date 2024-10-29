from typing import List

from app.models.literal import Literal
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.concepts.concept_service import ConceptService
from app.services.source_records.source_record_service import SourceRecordService

async def test_create_two_source_records_with_common_concepts_and_different_alt_labels(
        persisted_person_a_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model: SourceRecord,
        persisted_person_b_pydantic_model: Person,
        scanr_record_with_person_b_as_contributor_pydantic_model: SourceRecord
) -> None:
    """
    Given two persisted person pydantic_model,
    When a source record for person a with concepts is created
    And a source record for person b with a concept in common but with different alt_labels is created
    Then the records should share the same concept with all the alt_labels referenced.

    :param persisted_person_a_pydantic_model:
    :param scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model:
    :param persisted_person_b_pydantic_model:
    :param scanr_record_with_person_b_as_contributor_pydantic_model:
    :return:
    """
    def _get_alt_labels_to_check(existing_list, source_record) -> List[Literal]:
        for subject in source_record.subjects:
            if subject.uri == concept_uri:
                existing_list.extend(alt_label for alt_label in subject.alt_labels if
                                           alt_label not in existing_list)
        return existing_list

    record_service = SourceRecordService()
    concept_service = ConceptService()

    concept_uri = "http://www.idref.fr/02734004x/id"
    alt_labels_to_check = []
    alt_labels_to_check = _get_alt_labels_to_check(
        alt_labels_to_check,
        scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model
    )

    await record_service.create_source_record(
        source_record=scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_scanr_source_record_for_person_a = await record_service.get_source_record(
        scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model.uid)
    assert (
            fetched_scanr_source_record_for_person_a.uid ==
            scanr_record_with_person_a_as_contributor_and_additional_alt_labels_pydantic_model.uid
    )

    fetched_concept = await concept_service.get_concept(concept_uri)
    assert fetched_concept
    assert len(fetched_concept.alt_labels) == len(alt_labels_to_check)
    assert all(
        alt_label in fetched_concept.alt_labels for alt_label in alt_labels_to_check
    )

    await record_service.create_source_record(
        source_record=scanr_record_with_person_b_as_contributor_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
    fetched_scanr_source_record_for_person_b = await record_service.get_source_record(
        scanr_record_with_person_b_as_contributor_pydantic_model.uid)
    assert (
            fetched_scanr_source_record_for_person_b.uid ==
            scanr_record_with_person_b_as_contributor_pydantic_model.uid
    )
    alt_labels_to_check = _get_alt_labels_to_check(
        alt_labels_to_check,
        scanr_record_with_person_b_as_contributor_pydantic_model
    )

    fetched_concept = await concept_service.get_concept(concept_uri)
    assert fetched_concept
    assert len(fetched_concept.alt_labels) == len(alt_labels_to_check)
    assert all(
        alt_label in fetched_concept.alt_labels for alt_label in alt_labels_to_check
    )
