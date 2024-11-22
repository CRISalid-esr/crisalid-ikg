from app.models.identifier_types import PublicationIdentifierType
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_update_scanr_article_source_record(
        scanr_persisted_article_a_source_record_pydantic_model: SourceRecord,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
):
    """
        Given a valid source record model representing an article harvested from ScanR
        When asked for different field values
        Then the values should be returned correctly
        """
    service = SourceRecordService()
    common_uid = scanr_persisted_article_a_source_record_pydantic_model.uid
    assert scanr_article_a_v2_source_record_pydantic_model.uid == common_uid
    await service.update_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_source_record = await service.get_source_record(
        scanr_article_a_v2_source_record_pydantic_model.uid)
    assert fetched_source_record.source_identifier == "doi10.3847/1538-4357/ad0cc0"
    assert fetched_source_record.source_identifier == "doi10.3847/1538-4357/ad0cc0"
    assert fetched_source_record.harvester == "ScanR"
    # test title, abstracts, without order
    assert any(
        title.value == "All We Are Is Dust in the WIM: "
                       "Constraints on Dust Properties "
                       "in the Milky Way’s Warm Ionized Medium"
        and title.language == "en" for title in fetched_source_record.titles)
    assert any(
        title.value == "Tout ce que nous sommes est de la poussière dans le WIM : "
                       "contraintes sur les propriétés de la poussière "
                       "dans le milieu ionisé chaud de la Voie lactée"
        and title.language == "fr" for title in fetched_source_record.titles)
    assert any(
        abstract.value == "New abstract in English" and abstract.language == "en" for abstract in
        fetched_source_record.abstracts)
    assert any(
        abstract.value == "Nouveau résumé en français" and abstract.language == "fr" for abstract in
        fetched_source_record.abstracts)
    # test identifiers
    assert any(
        identifier.value == "hal-00000000" and identifier.type == PublicationIdentifierType.HAL for
        identifier in
        fetched_source_record.identifiers)
    assert any(
        identifier.value == "10.3847/1538-4357/ad0cc0"
        and identifier.type == PublicationIdentifierType.DOI
        for identifier in
        fetched_source_record.identifiers)


async def test_double_update_scanr_article_source_record(
        scanr_persisted_article_a_source_record_pydantic_model: SourceRecord,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        scanr_article_a_v3_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
):
    """
        Given a valid source record model representing an article harvested from ScanR
        When asked for different field values
        Then the values should be returned correctly
        """
    service = SourceRecordService()
    common_uid = scanr_persisted_article_a_source_record_pydantic_model.uid
    assert scanr_article_a_v2_source_record_pydantic_model.uid == common_uid
    await service.update_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    fetched_source_record_v2 = await service.get_source_record(
        scanr_article_a_v2_source_record_pydantic_model.uid)
    assert any(
        identifier.value == "hal-00000000" and identifier.type == PublicationIdentifierType.HAL for
        identifier in
        fetched_source_record_v2.identifiers)
    # test abstracts
    assert len(fetched_source_record_v2.abstracts) == len(
        scanr_article_a_v2_source_record_pydantic_model.abstracts)
    # test titles
    assert len(fetched_source_record_v2.titles) == len(
        scanr_article_a_v2_source_record_pydantic_model.titles)
    # test identifiers
    assert len(fetched_source_record_v2.identifiers) == len(
        scanr_article_a_v2_source_record_pydantic_model.identifiers)
    # test subjects
    assert len(fetched_source_record_v2.subjects) == len(
        scanr_article_a_v2_source_record_pydantic_model.subjects)

    assert scanr_article_a_v3_source_record_pydantic_model.uid == common_uid
    await service.update_source_record(
        source_record=scanr_article_a_v3_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model
    )
    fetched_source_record_v3 = await service.get_source_record(
        scanr_article_a_v3_source_record_pydantic_model.uid
    )
    assert not any(
        identifier.type == PublicationIdentifierType.HAL for
        identifier in
        fetched_source_record_v3.identifiers)

    assert len(scanr_article_a_v3_source_record_pydantic_model.subjects) == len(
        fetched_source_record_v3.subjects)

    assert len(fetched_source_record_v3.titles) == len(
        scanr_article_a_v3_source_record_pydantic_model.titles)

    assert len(fetched_source_record_v3.abstracts) == len(
        scanr_article_a_v3_source_record_pydantic_model.abstracts)


async def test_update_record_with_shared_concept(
        persisted_person_b_pydantic_model: Person,
        scanr_persisted_article_a_source_record_pydantic_model: SourceRecord,
        scanr_persisted_article_c_source_record_pydantic_model: SourceRecord,
        scanr_article_c_v2_source_record_pydantic_model: SourceRecord
):
    """
        Given two persisted source records with a shared concept
        When the update of scanr article c remove the relation to the shared concept and add a
        new concept
        Then the values should be returned correctly for both source records
    """
    service = SourceRecordService()
    shared_concept_uri = "http://www.idref.fr/027818055/id"

    fetched_source_record_a = await service.get_source_record(
        scanr_persisted_article_a_source_record_pydantic_model.uid)
    assert all(
        concept in fetched_source_record_a.subjects for concept in
        scanr_persisted_article_a_source_record_pydantic_model.subjects
    )

    fetched_source_record_c = await service.get_source_record(
        scanr_persisted_article_c_source_record_pydantic_model.uid)
    assert all(
        concept in fetched_source_record_c.subjects for concept in
        scanr_persisted_article_c_source_record_pydantic_model.subjects
    )
    assert any(
        shared_concept_uri == subject.uri for subject in fetched_source_record_a.subjects
    )
    assert any(
        shared_concept_uri == subject.uri for subject in fetched_source_record_c.subjects
    )

    await service.update_source_record(
        source_record=scanr_article_c_v2_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
    fetched_source_record_c_v2 = await service.get_source_record(
        scanr_article_c_v2_source_record_pydantic_model.uid)

    post_update_fetched_source_record_a = await service.get_source_record(
        scanr_persisted_article_a_source_record_pydantic_model.uid)
    assert post_update_fetched_source_record_a == fetched_source_record_a
    assert any(
        shared_concept_uri == subject.uri for subject in
        post_update_fetched_source_record_a.subjects
    )
    assert not any(
        shared_concept_uri == subject.uri for subject in fetched_source_record_c_v2.subjects
    )

    assert fetched_source_record_c.subjects != fetched_source_record_c_v2.subjects
    assert all(
        concept.uri in map(lambda x: x.uri, fetched_source_record_c_v2.subjects)
        for concept in scanr_article_c_v2_source_record_pydantic_model.subjects
    )


async def test_update_source_record_issue(
        persisted_person_a_pydantic_model: Person,
        scanr_persisted_article_a_source_record_pydantic_model: SourceRecord,
        scanr_article_a_source_record_with_updated_issue_pydantic_model: SourceRecord,
):
    """
    Given a persisted source record with an issue
    When the update of that source record update the issue
    Then the values should be updated and returned correctly
    """
    service = SourceRecordService()
    fetched_source_record = await service.get_source_record(
        scanr_persisted_article_a_source_record_pydantic_model.uid)
    assert fetched_source_record.uid == scanr_persisted_article_a_source_record_pydantic_model.uid
    assert (fetched_source_record.issue ==
            scanr_persisted_article_a_source_record_pydantic_model.issue)
    await service.update_source_record(
        source_record=scanr_article_a_source_record_with_updated_issue_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    fetched_source_record_updated = await service.get_source_record(
        scanr_article_a_source_record_with_updated_issue_pydantic_model.uid)
    assert fetched_source_record_updated.uid == fetched_source_record.uid
    assert fetched_source_record_updated.issue != fetched_source_record.issue
    assert (fetched_source_record_updated.issue.journal.uid ==
            fetched_source_record.issue.journal.uid)
    assert "Ceci est un titre d'issue" in fetched_source_record_updated.issue.titles
    assert fetched_source_record_updated.issue.volume == "1"
    assert "1" in fetched_source_record_updated.issue.number
