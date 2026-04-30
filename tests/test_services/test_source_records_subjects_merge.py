from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


# pylint: disable=too-many-arguments
async def test_create_multiple_source_records_with_a_common_subject(
        test_app,  # pylint: disable=unused-argument # connect signal listeners
        persisted_person_a_pydantic_model: Person,
        persisted_person_b_pydantic_model: Person,
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        hal_article_a_source_record_pydantic_model: SourceRecord,
        open_alex_article_a_source_record_pydantic_model: SourceRecord,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Given 3 source records with common hal identifier that have a common subject,
    When the source records are added to the graph
    Then the resulting document should cumulate the subjects of the source records.
    """
    source_record_service = SourceRecordService()
    await source_record_service.create_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model,
        identifier_used=default_identifier_used)

    await source_record_service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model,
        identifier_used=default_identifier_used)

    await source_record_service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model,
        identifier_used=default_identifier_used)

    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_document_by_source_record_uid(
        open_alex_article_a_source_record_pydantic_model.uid)
    assert document is not None
    distinct_concept_list = list(set(
        concept.uid for source_record in [
            hal_article_a_source_record_pydantic_model,
            scanr_article_a_v2_source_record_pydantic_model,
            open_alex_article_a_source_record_pydantic_model
        ] for concept in source_record.subjects
    ))
    assert len(document.subjects) == len(distinct_concept_list)
    assert all(subject.uid in distinct_concept_list for subject in document.subjects)
