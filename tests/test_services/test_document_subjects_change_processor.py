# file: tests/test_services/test_document_subjects_change_processor.py

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.change import Change, TargetType
from app.models.document import Document
from app.services.changes.processors.document_subjects_change_processor import (
    DocumentSubjectsChangeProcessor,
)


@pytest.mark.asyncio
async def test_document_subjects_change_processor_applies_subject_removal(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document
):
    """
    Given a document with multiple subjects,
    When a change requests to remove one subject,
    Then the subject is removed from the document node.
    """
    original_subject_uids = [subject.uid for subject in
                             document_hal_article_a_persisted_model.subjects]
    assert len(original_subject_uids) == 3

    subjects_to_remove = ["http://www.idref.fr/02734004x/id", "http://www.idref.fr/027818055/id"]

    change = Change(
        uid="test-change-001",
        target_uid=document_hal_article_a_persisted_model.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="001",
        action_type="REMOVE",
        path="subjects",
        parameters={"conceptUids": subjects_to_remove},
        timestamp="2023-10-01T12:00:00Z",
    )

    processor = DocumentSubjectsChangeProcessor(change)
    await processor.apply()

    # Reload the document to validate
    document_dao: DocumentDAO = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated_doc = await document_dao.get_document_by_uid(document_hal_article_a_persisted_model.uid)

    updated_subject_uids = [subject.uid for subject in updated_doc.subjects]
    assert set(updated_subject_uids) == {'http://www.wikidata.org/entity/Q210521'}


@pytest.mark.asyncio
async def test_document_subjects_change_processor_skips_unknown_subjects(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document
):
    """
    Given a document with multiple subjects,
    When a change requests to remove a subject that is not linked,
    Then the document's subjects remain unchanged.
    """
    original_subject_uids = [subject.uid for subject in
                             document_hal_article_a_persisted_model.subjects]
    assert len(original_subject_uids) == 3

    # Subject to remove is not among the original subjects
    change = Change(
        uid="test-change-002",
        target_uid=document_hal_article_a_persisted_model.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="002",
        action_type="UPDATE",
        path="subjects",
        parameters={"conceptUids": ["http://example.org/not-present"]},
        timestamp="2023-10-01T13:00:00Z",
    )

    processor = DocumentSubjectsChangeProcessor(change)
    await processor.apply()

    # Reload and validate
    document_dao: DocumentDAO = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated_doc = await document_dao.get_document_by_uid(document_hal_article_a_persisted_model.uid)

    updated_subject_uids = [subject.uid for subject in updated_doc.subjects]
    assert set(updated_subject_uids) == set(original_subject_uids)
