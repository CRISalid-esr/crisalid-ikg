from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.concepts.concept_service import ConceptService
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_two_source_records_with_same_concepts(
        persisted_person_a_pydantic_model: Person,
        persisted_person_b_pydantic_model: Person,
        scanr_record_with_person_a_as_contributor_pydantic_model: SourceRecord,
        scanr_record_with_person_b_as_contributor_pydantic_model: SourceRecord
) -> None:
    """
    Given two persisted person pydantic_model,
    When a source record for person a with concepts is created
    And a source record for person b with a concept in common but with a new pref_label is created
    Then the records should share the same concept with an updated pref_label.

    :param persisted_person_a_pydantic_model:
    :param idref_record_with_person_a_as_contributor_pydantic_model:
    :return:
    """
    record_service = SourceRecordService()
    concept_service = ConceptService()
    concept_uri = "http://www.idref.fr/02734004x/id"
    initial_pref_label = "Analyse des donn\u00e9es"
    updated_pref_label = "Analyse de donnée"

    await record_service.create_source_record(
        source_record=scanr_record_with_person_a_as_contributor_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_scanr_source_record_for_person_a = await record_service.get_source_record(
        scanr_record_with_person_a_as_contributor_pydantic_model.uid)
    assert (
            fetched_scanr_source_record_for_person_a.uid ==
            scanr_record_with_person_a_as_contributor_pydantic_model.uid
    )
    fetched_concept = await concept_service.get_concept(concept_uri)
    assert fetched_concept
    assert len(fetched_concept.pref_labels) == 1
    assert any(initial_pref_label == pref_label.value for pref_label in
               fetched_concept.pref_labels)
    await record_service.create_source_record(
        source_record=scanr_record_with_person_b_as_contributor_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
    fetched_scanr_source_record_for_person_b = await record_service.get_source_record(
        scanr_record_with_person_b_as_contributor_pydantic_model.uid)
    assert (
            fetched_scanr_source_record_for_person_b.uid ==
            scanr_record_with_person_b_as_contributor_pydantic_model.uid
    )
    fetched_concept = await concept_service.get_concept(concept_uri)
    assert fetched_concept
    assert len(fetched_concept.pref_labels) == 1
    assert any(updated_pref_label == pref_label.value for pref_label in
               fetched_concept.pref_labels)


async def test_create_two_source_records_with_common_concepts_and_different_alt_labels(
        persisted_person_a_pydantic_model: Person,
        scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model: SourceRecord,
        persisted_person_b_pydantic_model: Person,
        scanr_record_with_person_b_as_contributor_pydantic_model: SourceRecord
) -> None:
    """
    Given two persisted person pydantic_model,
    When a source record for person a with concepts is created
    And a source record for person b with a concept
    in common but with different alt_labels is created
    Then the records should share the same concept with all the alt_labels referenced.

    :param persisted_person_a_pydantic_model:
    :param scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model:
    :param persisted_person_b_pydantic_model:
    :param scanr_record_with_person_b_as_contributor_pydantic_model:
    :return:
    """

    record_service = SourceRecordService()
    concept_service = ConceptService()

    concept_uri = "http://www.idref.fr/02734004x/id"
    alt_labels_to_check = []

    subject = next(
        subject for subject in
        scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model.subjects
        if subject.uri == concept_uri
    )
    alt_labels_to_check.extend(
        alt_label
        for alt_label in subject.alt_labels if alt_label not in alt_labels_to_check
    )

    await record_service.create_source_record(
        source_record=scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_scanr_source_record_for_person_a = await record_service.get_source_record(
        scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model.uid)
    assert (
            fetched_scanr_source_record_for_person_a.uid ==
            scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model.uid
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

    subject = next(subject for subject in
                   scanr_record_with_person_b_as_contributor_pydantic_model.subjects
                   if subject.uri == concept_uri
                   )

    alt_labels_to_check.extend(
        alt_label
        for alt_label in subject.alt_labels if alt_label not in alt_labels_to_check
    )

    fetched_concept = await concept_service.get_concept(concept_uri)
    assert fetched_concept
    assert len(fetched_concept.alt_labels) == len(alt_labels_to_check)
    assert all(
        alt_label in fetched_concept.alt_labels for alt_label in alt_labels_to_check
    )
