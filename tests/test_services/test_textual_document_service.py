from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.documents.textual_document_service import TextualDocumentService
from app.services.source_records.equivalence_service import EquivalenceService
from app.signals import source_record_created, source_record_updated, \
    textual_document_sources_changed


async def test_update_textual_document(
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,  # pylint: disable=unused-argument
        source_record_id_doi_1_hal_1_persisted_model: SourceRecord
        # pylint: disable=unused-argument
) -> None:
    """
    Test that when 3 source_recorded are registered as equivalent, the textual document is
    recomputed from their metadata
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_persisted_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_hal_1_persisted_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    with source_record_updated.muted():
        with source_record_created.muted():
            with textual_document_sources_changed.muted():
                equivalence_service = EquivalenceService()
                factory = AbstractDAOFactory().get_dao_factory("neo4j")
                document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
                # update any of the source records, does not matter which one
                await equivalence_service.update_source_record(
                    None,
                    source_record_id_doi_1_persisted_model.uid)

                document = await document_dao.get_textual_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is True
                await TextualDocumentService().update_from_source_records(
                    None,
                    textual_document_uid=document.uid)
                document = await document_dao.get_textual_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is False
                assert len(document.titles) == 1
                assert document.titles[0].value == "Example Article with DOI and HAL"
