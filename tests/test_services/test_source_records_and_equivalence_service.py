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
    assert document.to_be_recomputed is True
    assert sorted(document.source_record_uids) == sorted([
        scanr_article_a_v2_source_record_pydantic_model.uid,
        hal_article_a_source_record_pydantic_model.uid,
        open_alex_article_a_source_record_pydantic_model.uid
    ])


async def test_create_source_records_with_one_having_common_id_with_others(
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
    assert document.to_be_recomputed is True
    assert sorted(document.source_record_uids) == sorted([
        scanr_article_a_source_record_pydantic_model.uid,
        open_alex_article_b_source_record_pydantic_model.uid,
        idref_article_a_source_record_pydantic_model.uid
    ])
