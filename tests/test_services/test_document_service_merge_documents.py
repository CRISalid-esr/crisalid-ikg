from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.documents.document_service import DocumentService


async def test_merge_documents(
        test_app,  # pylint: disable=unused-argument
        document_persisted_model,
        merged_hal_open_alex_persisted_model: Document,
) -> None:
    """
    Test that when when we merge two documents, the resulting document contains the
    union of the source records of the two initial documents
    :param document_persisted_model: Pydantic Document object for HAL article A
    :param merged_hal_open_alex_persisted_model: Pydantic Document object for the merge of
    HAL article A and OpenAlex article B
    """
    document_service = DocumentService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
    ## assert that merged_hal_open_alex_persisted_model contains the union of the source records
    # ['openalex-https://openalex.org/W123456789', 'hal-doi10.3847/1538-4357/ad0cc1']
    assert len(merged_hal_open_alex_persisted_model.source_record_uids) == 2
    assert ("openalex-https://openalex.org/W123456789" in
            merged_hal_open_alex_persisted_model.source_record_uids)
    assert ("hal-doi10.3847/1538-4357/ad0cc1" in
            merged_hal_open_alex_persisted_model.source_record_uids)
    # check that the inferred equivalents are correctly set up
    open_alex_inferred_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "openalex-https://openalex.org/W123456789",
        SourceRecordDAO.EquivalenceType.INFERRED
    )
    assert len(open_alex_inferred_equivalents) == 1
    assert "hal-doi10.3847/1538-4357/ad0cc1" in open_alex_inferred_equivalents
    # there should be no asserted equivalents at this point
    open_alex_asserted_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "openalex-https://openalex.org/W123456789",
        SourceRecordDAO.EquivalenceType.ASSERTED
    )
    assert len(open_alex_asserted_equivalents) == 0
    # for document_persisted_model, the source records are
    # ['scanr-source_record_id_doi_1']
    assert len(document_persisted_model.source_record_uids) == 1
    assert "scanr-source_record_id_doi_1" in document_persisted_model.source_record_uids
    # check that there are no inferred or asserted equivalents for this source record
    scanr_inferred_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "scanr-source_record_id_doi_1",
        SourceRecordDAO.EquivalenceType.INFERRED
    )
    assert len(scanr_inferred_equivalents) == 0
    scanr_asserted_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "scanr-source_record_id_doi_1",
        SourceRecordDAO.EquivalenceType.ASSERTED
    )
    assert len(scanr_asserted_equivalents) == 0
    # now merge the two documents
    await document_service.merge_documents(
        {document_persisted_model.uid, merged_hal_open_alex_persisted_model.uid}
    )
    # after the merge, the main document (the one with the largest number of source records)
    # should have received the source records of the other document
    survivor_document = await document_service.get_document(
        merged_hal_open_alex_persisted_model.uid)
    assert len(survivor_document.source_record_uids) == 3
    assert "openalex-https://openalex.org/W123456789" in survivor_document.source_record_uids
    assert "hal-doi10.3847/1538-4357/ad0cc1" in survivor_document.source_record_uids
    assert "scanr-source_record_id_doi_1" in survivor_document.source_record_uids
    # get the first source record and check its document uid points to the survivor document
    # the other document should be marked as "to_be_deleted"
    to_be_deleted_document = await document_service.get_document(document_persisted_model.uid)
    assert to_be_deleted_document.to_be_deleted is True
    # check that open_alex source record still has the same inferred equivalents
    # but has 2 asserted equivalents now
    open_alex_inferred_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "openalex-https://openalex.org/W123456789",
        SourceRecordDAO.EquivalenceType.INFERRED
    )
    assert len(open_alex_inferred_equivalents) == 1
    assert "hal-doi10.3847/1538-4357/ad0cc1" in open_alex_inferred_equivalents
    open_alex_asserted_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "openalex-https://openalex.org/W123456789",
        SourceRecordDAO.EquivalenceType.ASSERTED
    )
    assert len(open_alex_asserted_equivalents) == 2
    assert "hal-doi10.3847/1538-4357/ad0cc1" in open_alex_asserted_equivalents
    assert "scanr-source_record_id_doi_1" in open_alex_asserted_equivalents
    # check that hal source record still has the same inferred equivalents
    # but has 2 asserted equivalents now
    hal_inferred_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "hal-doi10.3847/1538-4357/ad0cc1",
        SourceRecordDAO.EquivalenceType.INFERRED
    )
    assert len(hal_inferred_equivalents) == 1
    assert "openalex-https://openalex.org/W123456789" in hal_inferred_equivalents
    hal_asserted_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "hal-doi10.3847/1538-4357/ad0cc1",
        SourceRecordDAO.EquivalenceType.ASSERTED
    )
    assert len(hal_asserted_equivalents) == 2
    assert "openalex-https://openalex.org/W123456789" in hal_asserted_equivalents
    assert "scanr-source_record_id_doi_1" in hal_asserted_equivalents
    # check that scanr source record has no inferred equivalents
    # but has 2 asserted equivalents now
    scanr_inferred_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "scanr-source_record_id_doi_1",
        SourceRecordDAO.EquivalenceType.INFERRED
    )
    assert len(scanr_inferred_equivalents) == 0
    scanr_asserted_equivalents = await source_record_dao.get_source_records_equivalent_uids(
        "scanr-source_record_id_doi_1",
        SourceRecordDAO.EquivalenceType.ASSERTED
    )
    assert len(scanr_asserted_equivalents) == 2
    assert "openalex-https://openalex.org/W123456789" in scanr_asserted_equivalents
    assert "hal-doi10.3847/1538-4357/ad0cc1" in scanr_asserted_equivalents
