import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.source_records.equivalence_service import EquivalenceService


@pytest.mark.current
async def test_infer_source_record_equivalents(
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,
        source_record_id_doi_1_hal_1_persisted_model: SourceRecord
) -> None:
    """
    Test that the equivalence service can infer equivalent source records
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_persisted_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_hal_1_persisted_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    service = EquivalenceService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    source_record_dao: SourceRecordDAO = factory.get_dao(SourceRecord)
    document_dao: DocumentDAO = factory.get_dao(Document)
    await service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    equivalent_uids = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert source_record_id_doi_1_hal_1_persisted_model.uid in equivalent_uids
    assert source_record_id_hal_1_persisted_model.uid in equivalent_uids
    document = await document_dao.get_textual_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    assert document is not None
    assert document.to_be_recomputed is True
