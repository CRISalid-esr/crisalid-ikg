from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.identifier_types import PublicationIdentifierType
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


async def test_create_multiple_source_records_with_common_id_for_multiple_person(
        persisted_person_a_pydantic_model: Person,
        persisted_person_b_pydantic_model: Person,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        hal_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_a_source_record_pydantic_model: SourceRecord
) -> None:
    """
    Given 3 source records with common hal identifier and created for different persons,
    When the source records are added to the graph
    Then the source records can be read and should be related to each other with a relationship.
    """
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    await source_record_service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)

    await source_record_service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)

    hal_fetched_source_record = await source_record_service.get_source_record(
        hal_article_a_source_record_pydantic_model.uid
    )

    scanr_fetched_source_record = await source_record_service.get_source_record(
        scanr_article_a_v2_source_record_pydantic_model.uid
    )

    open_alex_fetched_source_record = await source_record_service.get_source_record(
        open_alex_article_a_source_record_pydantic_model.uid
    )

    for record in [open_alex_fetched_source_record, scanr_fetched_source_record,
                   hal_fetched_source_record]:
        assert record
        assert any(
            fetched_identifier.type == PublicationIdentifierType.HAL
            and fetched_identifier.value == "hal-00000000"
            for fetched_identifier in record.identifiers
        )

    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_textual_document_by_source_record_uid(
        open_alex_article_a_source_record_pydantic_model.uid)
    assert document is not None
    assert sorted(document.source_record_uids) == sorted([
        scanr_article_a_v2_source_record_pydantic_model.uid,
        hal_article_a_source_record_pydantic_model.uid,
        open_alex_article_a_source_record_pydantic_model.uid
    ])


# pylint: disable=too-many-arguments
async def test_update_one_source_record_between_multiple_related_source_records(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        persisted_person_b_pydantic_model: Person,
        hal_persisted_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_persisted_article_a_source_record_pydantic_model: SourceRecord,
        scanr_persisted_article_a_v2_source_record_pydantic_model: SourceRecord,
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model: SourceRecord
) -> None:
    """
    Given 3 persisted source records with common hal identifier and a TextualDocument in common
    When one of the source records is updated
    Then the changes should be reflected to the source record, the existing TextualDocument
    should be updated in consequence and a new one should be created with the SourceRecord who
    lost the common identifier.
    """
    source_record_service = SourceRecordService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    initial_document = await document_dao.get_textual_document_by_source_record_uid(
        open_alex_persisted_article_a_source_record_pydantic_model.uid)
    assert initial_document is not None
    assert sorted(initial_document.source_record_uids) == sorted([
        scanr_persisted_article_a_v2_source_record_pydantic_model.uid,
        hal_persisted_article_a_source_record_pydantic_model.uid,
        open_alex_persisted_article_a_source_record_pydantic_model.uid
    ])

    await source_record_service.update_source_record(
        source_record=scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
    updated_fetched_source_record = await source_record_service.get_source_record(
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model.uid)
    assert updated_fetched_source_record

    new_document = await document_dao.get_textual_document_by_source_record_uid(
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model.uid
    )
    assert new_document
    assert new_document.uid != initial_document.uid
    assert new_document.source_record_uids == [
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model.uid
    ]

    initial_document_updated = await document_dao.get_textual_document_by_source_record_uid(
        open_alex_persisted_article_a_source_record_pydantic_model.uid)
    assert initial_document_updated != initial_document
    assert sorted(initial_document_updated.source_record_uids) == sorted([
        open_alex_persisted_article_a_source_record_pydantic_model.uid,
        hal_persisted_article_a_source_record_pydantic_model.uid
    ])


async def test_create_source_records_with_one_having_common_id_with_others(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        persisted_person_a_pydantic_model: Person,
        scanr_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_b_source_record_pydantic_model: SourceRecord,
        idref_article_a_source_record_pydantic_model: SourceRecord,
) -> None:
    """
    Given 3 source records harvested, with one of them having common identifiers with the other two,
    When the source records are added to the graph
    Then the source records are added, and they are related to each other with a relationship.
    """
    source_record_service = SourceRecordService()

    for record in [
        scanr_article_a_source_record_pydantic_model,
        open_alex_article_b_source_record_pydantic_model,
        idref_article_a_source_record_pydantic_model
    ]:
        await source_record_service.create_source_record(
            source_record=record,
            harvested_for=persisted_person_a_pydantic_model)

        assert await source_record_service.get_source_record(record.uid)

    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_textual_document_by_source_record_uid(
        scanr_article_a_source_record_pydantic_model.uid)
    assert document is not None
    assert sorted(document.source_record_uids) == sorted([
        scanr_article_a_source_record_pydantic_model.uid,
        open_alex_article_b_source_record_pydantic_model.uid,
        idref_article_a_source_record_pydantic_model.uid
    ])




async def test_create_source_record_with_common_id_with_persisted_source_records(
        test_app, # pylint: disable=unused-argument # connect signal listeners
        persisted_person_a_pydantic_model: Person,
        scanr_persisted_article_a_source_record_pydantic_model: SourceRecord,
        idref_persisted_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_b_source_record_pydantic_model: SourceRecord,
) -> None:
    """
    Given 2 persisted source record with no identifiers in common,
    When a new source record with identifiers in common with both persisted source records is added,
    Then the new source record is added, they becomre related to each other with relationship,
    and one of the existing document is updated and related to the 3 source records.
    """
    source_record_service = SourceRecordService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document_a = await document_dao.get_textual_document_by_source_record_uid(
        scanr_persisted_article_a_source_record_pydantic_model.uid)
    document_b = await document_dao.get_textual_document_by_source_record_uid(
        idref_persisted_article_a_source_record_pydantic_model.uid
    )
    assert document_a.uid != document_b.uid

    await source_record_service.create_source_record(
        source_record=open_alex_article_b_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)

    document_after_update = await document_dao.get_textual_document_by_source_record_uid(
        open_alex_article_b_source_record_pydantic_model.uid
    )
    assert document_after_update
    assert any(
        document_after_update.uid == record.uid
        for record in [document_a, document_b]
    )
    assert sorted(document_after_update.source_record_uids) == sorted([
        scanr_persisted_article_a_source_record_pydantic_model.uid,
        open_alex_article_b_source_record_pydantic_model.uid,
        idref_persisted_article_a_source_record_pydantic_model.uid
    ])
