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
