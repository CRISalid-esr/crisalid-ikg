# file: tests/test_amqp/test_amqp_user_actions_message_processor.py

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.amqp.amqp_user_actions_message_processor import AMQPUserActionsMessageProcessor
from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.change import Change, ChangeStatus
from app.models.document import Document


@pytest.mark.asyncio
async def test_amqp_user_actions_processor_applies_change(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
):  # pylint: disable=too-many-locals
    """
    Integration test for AMQPUserActionsMessageProcessor:
    Given a document in the graph with multiple subjects,
    When a valid AMQP user action message is received to remove subjects,
    Then the Change is applied and persisted, and the subjects are removed.
    """
    document = document_hal_article_a_persisted_model
    assert len(document.subjects) == 3

    subject_uids = [subject.uid for subject in document.subjects]
    # remove the first two subjects and keep the rest
    to_remove = subject_uids[:2]
    to_keep = subject_uids[2:]

    change_payload = {
        "uid": "amqp-change-001",
        "id": "001",
        "actionType": "REMOVE",
        "path": "subjects",
        "parameters": {
            "conceptUids": to_remove
        },
        "personUid": "person:test",
        "targetType": "DOCUMENT",
        "targetUid": document.uid,
        "timestamp": "2023-10-01T12:00:00Z",
        "application": "pytest"
    }

    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPUserActionsMessageProcessor(queue, settings)

    payload = json.dumps(change_payload).encode("utf-8")
    # pylint: disable=protected-access
    await processor._process_message("event.documents.document.updated", payload)

    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    updated = await document_dao.get_document_by_uid(document.uid)
    assert updated is not None

    updated_uids = [subj.uid for subj in updated.subjects]
    assert all(uid in updated_uids for uid in to_keep)
    assert all(uid not in updated_uids for uid in to_remove)

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change_payload["uid"])
    assert stored is not None
    assert stored.status == ChangeStatus.APPLIED


@pytest.fixture(name="mocked_fetch_publications")
def mocked_fetch_publications_fixture():
    """
    Fixture to mock the `amqp_interface.fetch_publications` signal receiver.
    """
    with patch("app.amqp.amqp_interface.AMQPInterface.fetch_publications",
               new_callable=AsyncMock) as mocked:
        yield mocked


@pytest.mark.asyncio
async def test_amqp_user_actions_processor_fetch_triggers_signal(
        mocked_fetch_publications,
        test_app,  # pylint: disable=unused-argument
):
    """
    Integration test for FETCH actionType:
    Ensure that processing a FETCH message triggers the
    AMQPInterface.fetch_publications signal receiver.
    """
    payload = {
        "uid": "amqp-fetch-001",
        "id": "001",
        "actionType": "FETCH",
        "path": None,
        "parameters": {
            "platforms": ["hal", "scanr", "idref"]
        },
        "personUid": "person:test",
        "targetType": "HARVESTING",
        "targetUid": "person:test",
        "timestamp": "2023-10-01T12:00:00Z",
        "application": "pytest"
    }

    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPUserActionsMessageProcessor(queue, settings)

    payload_bytes = json.dumps(payload).encode("utf-8")
    # pylint: disable=protected-access
    await processor._process_message("event.person.fetch", payload_bytes)
    mocked_fetch_publications.assert_awaited_once()
    _, kwargs = mocked_fetch_publications.call_args
    assert "payload" in kwargs
    assert kwargs["payload"]["person_uid"] == "person:test"
    assert kwargs["payload"]["harvesters"] == ["hal", "scanr", "idref"]


@pytest.fixture(name="mocked_authenticate_orcid")
def mocked_authenticate_orcid_fixture():
    """
    Fixture to mock the `amqp_interface.fetch_publications` signal receiver.
    """
    with patch("app.services.people.people_service.PeopleService.authenticate_orcid",
               new_callable=AsyncMock) as mocked:
        yield mocked


@pytest.mark.asyncio
async def test_amqp_user_actions_processor_authenticate_orcid(
        mocked_authenticate_orcid,
        test_app,  # pylint: disable=unused-argument
):
    """
    Integration test for ADD actionType to authenticate an ORCID identifier
    """
    payload = {
        "actionType": "ADD",
        "targetType": "PERSON",
        "targetUid": "local-jdoe@univ-domain.edu",
        "path": "identifiers",
        "parameters": {
            "identifier": {
                "type": "ORCID",
                "value": "0000-0001-2345-6789"
            }
        },
        "timestamp": "2025-08-26T06:17:28.243Z",
        "personUid": "local-jdoe@univ-domain.edu",
        "application": "sovisuplus"
    }

    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPUserActionsMessageProcessor(queue, settings)

    payload_bytes = json.dumps(payload).encode("utf-8")
    # pylint: disable=protected-access
    await processor._process_message("task.people.person.*", payload_bytes)

    mocked_authenticate_orcid.assert_awaited_once()
    args, _ = mocked_authenticate_orcid.call_args
    assert args == ('local-jdoe@univ-domain.edu', '0000-0001-2345-6789', '2025-08-26T06:17:28.243Z')


@pytest.mark.asyncio
async def test_amqp_user_actions_processor_merges_document_triggers_registered_change(
        test_app  # pylint: disable=unused-argument
):
    """
    Regression test:
    Given a MERGE action on a DOCUMENT,
    When the message is processed,
    Then ChangeService.create_and_apply_change should be awaited with a Change instance.
    """
    payload = {
        "id": "374606b8-098c-4287-86ce-1b66c6e49490",
        "actionType": "MERGE",
        "targetType": "DOCUMENT",
        "targetUid": "79098c18-a4ed-4bf2-b927-8ce473fa8110",
        "path": None,
        "parameters": {
            "mergedDocumentUids": ["5fe031b8-597e-449c-917d-2826f7b43b15"]
        },
        "timestamp": "2025-10-19T16:31:27.509Z",
        "personUid": "local-jdornbusch",
        "application": "sovisuplus",
    }

    queue = asyncio.Queue()
    settings = get_app_settings()
    processor = AMQPUserActionsMessageProcessor(queue, settings)

    with patch("app.services.changes.change_service.ChangeService.create_and_apply_change",
               new_callable=AsyncMock) as mocked_apply:
        # pylint: disable=protected-access
        await processor._process_message("event.documents.document.merged",
                                         json.dumps(payload).encode("utf-8"))

        mocked_apply.assert_awaited_once()
        (change_arg,), _ = mocked_apply.await_args
        assert isinstance(change_arg, Change)
