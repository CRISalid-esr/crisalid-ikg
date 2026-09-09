from datetime import datetime
from typing import cast

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.agent_identifiers import PersonIdentifier
from app.models.document import Document
from app.models.journal_article import JournalArticle
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.equivalence_service import EquivalenceService
from app.services.source_records.source_record_service import SourceRecordService


async def test_infer_source_record_equivalents(
        test_app,  # pylint: disable=unused-argument
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
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    await service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    equivalent_uids = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert source_record_id_doi_1_hal_1_persisted_model.uid in equivalent_uids
    assert source_record_id_hal_1_persisted_model.uid in equivalent_uids
    document = await document_dao.get_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    assert document is not None
    assert sorted(document.source_record_uids) == sorted([
        source_record_id_doi_1_persisted_model.uid,
        source_record_id_hal_1_persisted_model.uid,
        source_record_id_doi_1_hal_1_persisted_model.uid
    ])
    assert document.uid is not None
    assert len(document.titles) == 1
    assert document.titles[0].value == "Example Article with DOI and HAL"
    assert document.publication_date is not None
    assert document.publication_date == "2019-02"
    assert isinstance(document.publication_date_start, datetime)
    assert isinstance(document.publication_date_end, datetime)
    assert document.publication_date_end.isoformat() == "2019-02-28T23:59:59"
    assert document.publication_date_start.isoformat() == "2019-02-01T00:00:00"
    assert document.type == "JournalArticle"


async def test_attach_new_source_record_to_existing_document(
        test_app,  # pylint: disable=unused-argument
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Test that the equivalence service can infer equivalent source records
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_doi_1_hal_1_pydantic_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    source_record_service = SourceRecordService()
    equivalence_service = EquivalenceService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    await equivalence_service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    equivalent_uids = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert len(equivalent_uids) == 0
    await source_record_service.create_source_record(source_record_id_doi_1_hal_1_pydantic_model,
                                                     persisted_person_a_pydantic_model,
                                                     default_identifier_used)
    # equivalence service will not be called automatically as blinker signals are not connected
    await equivalence_service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    equivalent_uids = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert source_record_id_doi_1_hal_1_pydantic_model.uid in equivalent_uids
    document = await document_dao.get_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    assert document is not None
    assert len(document.titles) == 1
    assert document.titles[0].value == "Example Article with DOI and HAL"
    assert sorted(document.source_record_uids) == sorted([
        source_record_id_doi_1_persisted_model.uid,
        source_record_id_doi_1_hal_1_pydantic_model.uid
    ])
    source_record_uids = await source_record_dao.get_source_record_uids_by_document_uid(
        document.uid)
    assert source_record_uids is not None
    assert sorted(source_record_uid for source_record_uid in source_record_uids) == sorted([
        source_record_id_doi_1_persisted_model.uid,
        source_record_id_doi_1_hal_1_pydantic_model.uid
    ])
    assert isinstance(document, JournalArticle)
    assert document.type == "JournalArticle"


async def test_merge_two_existing_documents(
        test_app,  # pylint: disable=unused-argument
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person,
        default_identifier_used: PersonIdentifier
) -> None:
    """
    Test that the equivalence service can infer equivalent source records
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_doi_1_hal_1_pydantic_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    source_record_service = SourceRecordService()
    equivalence_service = EquivalenceService()
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    await equivalence_service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    await equivalence_service.update_source_record(None, source_record_id_hal_1_persisted_model.uid)
    # for the moment, the two documents have no equivalents
    equivalent_uids_1 = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert len(equivalent_uids_1) == 0
    equivalent_uids_2 = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_hal_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert len(equivalent_uids_2) == 0
    # create a new source record with the same identifiers as the two existing ones
    await source_record_service.create_source_record(source_record_id_doi_1_hal_1_pydantic_model,
                                                     persisted_person_a_pydantic_model,
                                                     default_identifier_used)
    # equivalence service will not be called automatically as blinker signals are not connected
    await equivalence_service.update_source_record(None, source_record_id_doi_1_persisted_model.uid)
    equivalent_uids_1 = await source_record_dao.get_source_records_equivalent_uids(
        source_record_id_doi_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)
    assert source_record_id_doi_1_hal_1_pydantic_model.uid in equivalent_uids_1
    document = await document_dao.get_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    assert document is not None
    assert sorted(document.source_record_uids) == sorted([
        source_record_id_doi_1_persisted_model.uid,
        source_record_id_hal_1_persisted_model.uid,
        source_record_id_doi_1_hal_1_pydantic_model.uid
    ])
    assert len(document.titles) == 1
    assert document.titles[0].value == "Example Article with DOI and HAL"
    source_record_uids = await source_record_dao.get_source_record_uids_by_document_uid(
        document.uid)
    assert source_record_uids is not None
    assert sorted(source_record_uid for source_record_uid in source_record_uids) == sorted([
        source_record_id_doi_1_persisted_model.uid,
        source_record_id_hal_1_persisted_model.uid,
        source_record_id_doi_1_hal_1_pydantic_model.uid
    ])
    assert isinstance(document, JournalArticle)
    assert document.type == "JournalArticle"
