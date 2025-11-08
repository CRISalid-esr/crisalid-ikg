# file: tests/test_services/test_change_service.py
from unittest.mock import patch, AsyncMock

import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.book_of_chapters import BookOfChapters
from app.models.change import Change, TargetType, ChangeStatus
from app.models.document import Document
from app.models.journal_article import JournalArticle
from app.services.changes.change_service import ChangeService


@pytest.fixture(name="mocked_document_updated_signal")
def mocked_document_updated_signal_fixture():
    """
    Fixture to mock the `document_updated` signal.
    """
    with patch("app.signals.document_updated.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


@pytest.mark.asyncio
# @pytest.mark.current
async def test_change_service_removes_subjects_from_document(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:
    """
    Given a document with multiple subjects,
    When a Change is submitted to ChangeService to remove some of them,
    Then the document node no longer has those subjects.
    """
    document = document_hal_article_a_persisted_model
    assert len(document.subjects) >= 2

    subject_uids = [subject.uid for subject in document.subjects]
    to_remove = subject_uids[:2]
    to_keep = subject_uids[2:]

    change = Change(
        uid="change-service-test-001",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="001",
        action_type="REMOVE",
        path="subjects",
        parameters={"conceptUids": to_remove},
        timestamp="2023-10-01T12:00:00Z",
    )

    service = ChangeService()
    await service.create_and_apply_change(change)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated = await document_dao.get_document_by_uid(document.uid)
    assert updated is not None

    updated_uids = [subj.uid for subj in updated.subjects]
    assert all(uid in updated_uids for uid in to_keep)
    assert all(uid not in updated_uids for uid in to_remove)

    mocked_document_updated_signal.assert_called_once_with(service, document_uid=document.uid)

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored is not None
    assert stored.status == ChangeStatus.APPLIED

@pytest.mark.asyncio
async def test_change_service_raises_if_document_does_not_exist(
        test_app,  # pylint: disable=unused-argument
        mocked_document_updated_signal  # ensures isolation
) -> None:
    """
    Given a Change targeting a non-existent document UID,
    When ChangeService tries to apply the Change,
    Then a ValueError is raised.
    """
    nonexistent_uid = "nonexistent-document-uid"

    change = Change(
        uid="change-service-test-002",
        target_uid=nonexistent_uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="002",
        action_type="REMOVE",
        path="subjects",
        parameters={"conceptUids": ["http://example.org/concept/abc"]},
        timestamp="2023-10-01T12:00:00Z",
    )

    service = ChangeService()

    with pytest.raises(ValueError, match=f"Target document {nonexistent_uid} does not exist"):
        await service.create_and_apply_change(change)

    # Signal should not have been triggered
    mocked_document_updated_signal.assert_not_called()


@pytest.mark.asyncio
async def test_change_service_update_type_of_document(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:
    """
    Given a document with a certain type,
    When a Change is submitted to ChangeService to update the type
    Then the document node has a new type and the object is of a different class when hydrated
    """
    document = document_hal_article_a_persisted_model
    assert document.type == "JournalArticle"

    change = Change(
        uid="change-service-test-003",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="003",
        action_type="UPDATE",
        path="documentType",
        parameters={"value": "BookOfChapters"},
        timestamp="2023-10-01T12:00:00Z",
    )

    service = ChangeService()
    await service.create_and_apply_change(change)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated = await document_dao.get_document_by_uid(document.uid)
    assert updated is not None
    assert updated.type == "BookOfChapters"
    assert updated.__class__ == BookOfChapters

    mocked_document_updated_signal.assert_called_once_with(service, document_uid=document.uid)

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored is not None
    assert stored.status == ChangeStatus.APPLIED


@pytest.mark.asyncio
async def test_change_service_update_invalid_type_of_document(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document) -> None:
    """
    Given a document with a certain type,
    When a Change is submitted to ChangeService to update the type and the type is incorrect
    Then a ValueError is raised and the document is not modified
    """
    document = document_hal_article_a_persisted_model
    assert document.type == "JournalArticle"

    change = Change(
        uid="change-service-test-004",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="004",
        action_type="UPDATE",
        path="documentType",
        parameters={"value": "Not_a_correct_type"},
        timestamp="2023-10-01T12:00:00Z",
    )

    service = ChangeService()
    with pytest.raises(ValueError):
        await service.create_and_apply_change(change)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated = await document_dao.get_document_by_uid(document.uid)
    assert updated is not None
    assert updated.type == "JournalArticle"
    assert updated.__class__ == JournalArticle

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored is not None
    assert stored.status == ChangeStatus.FAILED


@pytest.mark.asyncio
@pytest.mark.current
async def test_change_service_add_subject_to_document(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:
    """
    Given a document with multiple subjects,
    When a Change is submitted to ChangeService to remove some of them,
    Then the document node no longer has those subjects.
    """
    document = document_hal_article_a_persisted_model
    assert len(document.subjects) == 3

    change = Change(
        uid="change-service-test-005",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="005",
        action_type="ADD",
        path="subjects",
        parameters={"uid":"http://vocab.getty.edu/aat/300054595",
                    "uri":"http://vocab.getty.edu/aat/300054595",
                    "prefLabels":[{"value":"analysis","language":"en"}],
                    "altLabels":[]},
        timestamp="2023-10-01T12:00:00Z",
    )

    service = ChangeService()
    await service.create_and_apply_change(change)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated = await document_dao.get_document_by_uid(document.uid)
    assert updated is not None

    updated_uids = [subj.uid for subj in updated.subjects]
    assert len(updated_uids) == len(document.subjects) + 1
    assert change.parameters.get('uid') in updated_uids

    mocked_document_updated_signal.assert_called_once_with(service, document_uid=document.uid)

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored is not None
    assert stored.status == ChangeStatus.APPLIED

@pytest.mark.asyncio
@pytest.mark.current
async def test_change_service_add_same_subject_twice(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal) -> None:
    """
    Given a document with multiple subjects,
    When the same ADD Change is applied twice with identical parameters,
    Then the document only contains one instance of the added subject (no duplicates).
    """
    document = document_hal_article_a_persisted_model
    assert len(document.subjects) == 3

    change_parameters = {
        "uid": "http://vocab.getty.edu/aat/300054595",
        "uri": "http://vocab.getty.edu/aat/300054595",
        "prefLabels": [{"value": "analysis", "language": "en"}],
        "altLabels": [],
    }

    first_change = Change(
        uid="change-service-test-006a",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="006a",
        action_type="ADD",
        path="subjects",
        parameters=change_parameters,
        timestamp="2023-10-01T12:00:00Z",
    )

    second_change = Change(
        uid="change-service-test-006b",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="person:test",
        application="pytest",
        id="006b",
        action_type="ADD",
        path="subjects",
        parameters=change_parameters,
        timestamp="2023-10-01T12:01:00Z",
    )

    service = ChangeService()
    await service.create_and_apply_change(first_change)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated1 = await document_dao.get_document_by_uid(document.uid)
    assert updated1 is not None

    updated_uids1 = [subj.uid for subj in updated1.subjects]
    assert len(updated_uids1) == len(document.subjects) + 1
    assert change_parameters["uid"] in updated_uids1

    assert mocked_document_updated_signal.call_count == 1

    await service.create_and_apply_change(second_change)

    updated2 = await document_dao.get_document_by_uid(document.uid)
    assert updated2 is not None

    updated_uids2 = [subj.uid for subj in updated2.subjects]
    assert len(updated_uids2) == len(document.subjects) + 1
    assert change_parameters["uid"] in updated_uids2

    assert mocked_document_updated_signal.call_count == 2
