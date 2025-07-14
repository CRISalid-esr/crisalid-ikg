# file: tests/test_amqp/test_amqp_user_actions_message_processor.py

import asyncio
import json

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
        "action": "UPDATE",
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
