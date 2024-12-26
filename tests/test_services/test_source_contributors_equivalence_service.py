from typing import cast

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService


@pytest.mark.current
async def test_create_source_records_with_shared_contributors(
        # pylint: disable=too-many-arguments
        test_app,  # pylint: disable=unused-argument
        persisted_person_d_pydantic_model: Person,
        persisted_person_e_pydantic_model: Person,
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
        harvested_for=persisted_person_e_pydantic_model)

    await source_record_service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_d_pydantic_model)

    await source_record_service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_d_pydantic_model)
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    document = await document_dao.get_textual_document_by_source_record_uid(
        hal_article_a_source_record_pydantic_model.uid)
    assert document is not None
    assert len(document.contributions) == 10
    contribution = next(
        (contribution for contribution in document.contributions if
         contribution.contributor.uid == persisted_person_d_pydantic_model.uid),
        None)
    assert contribution is not None
    assert contribution.roles is not None
    assert len(contribution.roles) == 1
    assert contribution.roles[0].value == "http://id.loc.gov/vocabulary/relators/aut"
    assert contribution.contributor.uid == persisted_person_d_pydantic_model.uid
    assert contribution.contributor.display_name == "Garcia, Raymond"
    assert contribution.contributor.external is False

    print("pause")
