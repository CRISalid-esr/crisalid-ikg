from datetime import datetime
from typing import cast

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.document import Document
from app.models.identifier_types import PublicationIdentifierType
from app.models.journal_article import JournalArticle
from app.models.open_access_status import OAStatus, UnpaywallOAStatus
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.documents.document_service import DocumentService
from app.services.source_records.equivalence_service import EquivalenceService
from app.services.source_records.source_record_service import SourceRecordService
from app.signals import source_record_created, source_record_updated, \
    document_sources_changed


async def test_update_document(
        source_record_id_doi_1_persisted_model: SourceRecord,
        source_record_id_hal_1_persisted_model: SourceRecord,  # pylint: disable=unused-argument
        source_record_id_doi_1_hal_1_persisted_model: SourceRecord
        # pylint: disable=unused-argument
) -> None:
    """
    Test that when 3 source_recorded are registered as equivalent, the document is
    recomputed from their metadata
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_persisted_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_hal_1_persisted_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    with source_record_updated.muted():
        with source_record_created.muted():
            with document_sources_changed.muted():
                equivalence_service = EquivalenceService()
                factory = AbstractDAOFactory().get_dao_factory("neo4j")
                document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
                # update any of the source records, does not matter which one
                await equivalence_service.update_source_record(
                    None,
                    source_record_id_doi_1_persisted_model.uid)

                document = await document_dao.get_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is True
                await DocumentService().update_from_source_records(
                    None,
                    document_uid=document.uid)
                document = await document_dao.get_document_by_source_record_uid(
                    source_record_id_doi_1_persisted_model.uid)
                assert document is not None
                assert document.to_be_recomputed is False
                assert len(document.titles) == 1
                assert document.titles[0].value == "Example Article with DOI and HAL"
                assert document.publication_date is not None
                assert document.publication_date == "2019-02"
                assert isinstance(document.publication_date_start, datetime)
                assert isinstance(document.publication_date_end, datetime)
                assert document.publication_date_end.isoformat() == "2019-02-28T23:59:59"
                assert document.publication_date_start.isoformat() == "2019-02-01T00:00:00"
                assert isinstance(document, JournalArticle)
                assert document.type == "JournalArticle"
                assert len(document.subjects) == 4
                assert all(subject.uid in [
                    "http://www.idref.fr/concept-a/id",
                    "http://www.idref.fr/concept-b/id",
                    "http://www.idref.fr/concept-d/id",
                    "http://www.idref.fr/concept-e/id"
                ] for subject in document.subjects)

@pytest.mark.current
async def test_get_document_uid_from_person_uid(
        hal_article_a_source_record_persisted_model: SourceRecord,
        # pylint: disable=unused-argument
) -> None:
    """
    Test that from a person_uid, uids of linked documents are returned
    :param source_record_id_doi_1_persisted_model: Pydantic SourceRecord object with DOI identifier
    :param source_record_id_hal_1_persisted_model: Pydantic SourceRecord object with HAL identifier
    :param source_record_id_doi_1_hal_1_persisted_model: Pydantic SourceRecord object with both
    DOI and HAL identifiers (the same as the other two)
    """
    with source_record_updated.muted():
        with source_record_created.muted():
            with document_sources_changed.muted():
                equivalence_service = EquivalenceService()
                factory = AbstractDAOFactory().get_dao_factory("neo4j")
                document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
                # update any of the source records, does not matter which one
                await equivalence_service.update_source_record(
                    None,
                    hal_article_a_source_record_persisted_model.uid)
                document = await document_dao.get_document_by_source_record_uid(
                    hal_article_a_source_record_persisted_model.uid)
                await DocumentService().update_from_source_records(
                    None,
                    document_uid=document.uid)

                document_service = DocumentService()
                document_uids = await document_service.get_document_uids_of_person(
                    person_uid='hal-43b38a7c4e694812ba4a2fe8c40ab09d')
                assert len(document_uids) == 1


async def test_oa_status_document_with_no_doi_and_no_hal(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
) -> None:
    """
    Test that when a journal is created from source records with no doi and no file in hal,
    then the Open Access status is CLOSED.
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    hal_article_with_journal_1_pydantic_model.identifiers = [
        id for id in hal_article_with_journal_1_pydantic_model.identifiers
        if id.type != PublicationIdentifierType.DOI
    ]
    open_alex_article_with_journal_1_pydantic_model.identifiers = [
        id for id in open_alex_article_with_journal_1_pydantic_model.identifiers
        if id.type != PublicationIdentifierType.DOI
    ]

    service = EquivalenceService()
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))

    await service.update_source_record(None, hal_article_with_journal_1_persisted_model.uid)
    await source_record_dao.get_source_records_equivalent_uids(
        hal_article_with_journal_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.open_access_status.oa_computed_status
    assert document.open_access_status.oa_status == OAStatus.CLOSED
    assert document.open_access_status.upw_oa_status is None
    assert not document.open_access_status.oa_upw_success_status
    assert document.open_access_status.oa_doaj_success_status is None

async def test_oa_status_document_with_no_doi_but_hal(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
) -> None:
    """
    Test that when a journal is created from source records with no doi but a file in hal,
    then Open Access Status is Green
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """
    hal_article_with_journal_1_pydantic_model.identifiers = [
        id for id in hal_article_with_journal_1_pydantic_model.identifiers
        if id.type != PublicationIdentifierType.DOI
    ]
    hal_article_with_journal_1_pydantic_model.custom_metadata.hal_submit_type = 'file'

    open_alex_article_with_journal_1_pydantic_model.identifiers = [
        id for id in open_alex_article_with_journal_1_pydantic_model.identifiers
        if id.type != PublicationIdentifierType.DOI
    ]


    service = EquivalenceService()
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))

    await service.update_source_record(None, hal_article_with_journal_1_persisted_model.uid)
    await source_record_dao.get_source_records_equivalent_uids(
        hal_article_with_journal_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.open_access_status.oa_computed_status
    assert document.open_access_status.oa_status == OAStatus.GREEN
    assert document.open_access_status.upw_oa_status is None
    assert not document.open_access_status.oa_upw_success_status
    assert document.open_access_status.oa_doaj_success_status is None


async def test_oa_status_document_with_doi_but_no_hal(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
) -> None:
    """
    Test that when a journal is created from source records with no doi and no file in
    hal but a repository in Unpaywall, the Open Access status depends on Unpaywall data.
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """

    for identifier in hal_article_with_journal_1_pydantic_model.identifiers:
        if identifier.type == PublicationIdentifierType.DOI:
            identifier.value = "10.1017/ash.2023.207"

    for identifier in open_alex_article_with_journal_1_pydantic_model.identifiers:
        if identifier.type == PublicationIdentifierType.DOI:
            identifier.value = "10.1017/ash.2023.207"

    service = EquivalenceService()
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))

    await service.update_source_record(None, hal_article_with_journal_1_persisted_model.uid)
    await source_record_dao.get_source_records_equivalent_uids(
        hal_article_with_journal_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.open_access_status.oa_computed_status
    assert document.open_access_status.oa_status == OAStatus.GREEN
    assert document.open_access_status.upw_oa_status == UnpaywallOAStatus.GOLD
    assert document.open_access_status.oa_upw_success_status
    assert document.open_access_status.oa_doaj_success_status


async def test_oa_status_document_with_doi_not_in_upw_and_no_hal(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person,
) -> None:
    """
    Test that when a journal is created from source records with no file in hal and the doi
    that does not return anything from unpaywall, then the Open Access status is CLOSED
    :param hal_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    HAL with journal information and DOI identifier (carries volume information)
    :param open_alex_article_with_journal_1_pydantic_model: Pydantic SourceRecord object from
    OpenAlex with journal information and the same DOI identifier (carries number information)
    """

    for identifier in hal_article_with_journal_1_pydantic_model.identifiers:
        if identifier.type == PublicationIdentifierType.DOI:
            identifier.value = "10.1017/ash.2023.208"

    for identifier in open_alex_article_with_journal_1_pydantic_model.identifiers:
        if identifier.type == PublicationIdentifierType.DOI:
            identifier.value = "10.1017/ash.2023.208"

    service = EquivalenceService()
    source_record_service = SourceRecordService()
    hal_article_with_journal_1_persisted_model = await (
        source_record_service.create_source_record(
            hal_article_with_journal_1_pydantic_model,
            persisted_person_f_pydantic_model
        ))
    await source_record_service.create_source_record(
        open_alex_article_with_journal_1_pydantic_model,
        persisted_person_f_pydantic_model
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    document_dao: DocumentDAO = cast(DocumentDAO, factory.get_dao(Document))
    source_record_dao: SourceRecordDAO = cast(SourceRecordDAO, factory.get_dao(SourceRecord))

    await service.update_source_record(None, hal_article_with_journal_1_persisted_model.uid)
    await source_record_dao.get_source_records_equivalent_uids(
        hal_article_with_journal_1_persisted_model.uid, SourceRecordDAO.EquivalenceType.INFERRED)

    document = await document_dao.get_document_by_source_record_uid(
        hal_article_with_journal_1_persisted_model.uid)
    document_service = DocumentService()
    await document_service.update_from_source_records(
        None,
        document_uid=document.uid
    )
    document = await document_dao.get_document_by_uid(document.uid)
    assert document is not None
    assert document.open_access_status.oa_computed_status
    assert document.open_access_status.oa_status is OAStatus.CLOSED
    assert document.open_access_status.upw_oa_status is None
    assert not document.open_access_status.oa_upw_success_status
    assert document.open_access_status.oa_doaj_success_status is None
