# file: tests/test_services/test_change_error_reporting.py
import asyncio
import json
from unittest.mock import patch, AsyncMock

import pytest

from app.amqp.amqp_user_actions_message_processor import AMQPUserActionsMessageProcessor
from app.amqp.message_mode import MessageMode
from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.change import Change, TargetType, ChangeStatus
from app.models.document import Document
from app.models.people import Person
from app.services.changes.change_service import ChangeService

AUT = "http://id.loc.gov/vocabulary/relators/aut"


@pytest.fixture(name="mocked_document_updated_signal")
def mocked_document_updated_signal_fixture():
    """Mock the `document_updated` signal."""
    with patch("app.signals.document_updated.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


@pytest.fixture(name="mocked_change_applied_signal")
def mocked_change_applied_signal_fixture():
    """Mock the `change_applied` signal."""
    with patch("app.signals.change_applied.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


@pytest.fixture(name="mocked_change_failed_signal")
def mocked_change_failed_signal_fixture():
    """Mock the `change_failed` signal."""
    with patch("app.signals.change_failed.send_async", new_callable=AsyncMock) as mocked_signal:
        yield mocked_signal


def _contributions_change(document_uid: str, contributions: list[dict],
                          uid: str = "sovisuplus:err1",
                          change_id: str = "err1",
                          timestamp: str = "2026-01-01T09:00:00Z") -> Change:
    return Change(
        uid=uid,
        target_uid=document_uid,
        target_type=TargetType.DOCUMENT,
        person_uid="local-user1",
        application="sovisuplus",
        id=change_id,
        action_type="UPDATE",
        path="contributions",
        parameters={"contributions": contributions},
        timestamp=timestamp,
    )


async def _contributor_uids(document_uid: str) -> set:
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_uid(document_uid)
    return {contribution.contributor.uid for contribution in document.contributions}


@pytest.mark.asyncio
async def test_partial_failure_records_warnings_and_emits_applied_event(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal,  # pylint: disable=unused-argument
        mocked_change_applied_signal,
        mocked_change_failed_signal) -> None:
    """
    Given a contributions change where one person resolves and one cannot be created
        (no display name),
    When the change is applied,
    Then the change is APPLIED with a warning, the warning is persisted on the Change node,
        and the change_applied event carries the warning.
    """
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model

    contributions = [
        {"rank": 0, "roles": [AUT],
         "person": {"uid": internal.uid, "displayName": internal.display_name,
                    "identifiers": []},
         "affiliations": []},
        {"rank": 1, "roles": [AUT],
         "person": {"uid": None, "displayName": None,
                    "identifiers": [{"type": "orcid", "value": "0000-0000-0000-0099"}]},
         "affiliations": []},
    ]
    service = ChangeService()
    change = _contributions_change(document.uid, contributions)
    await service.create_and_apply_change(change)

    assert await _contributor_uids(document.uid) == {internal.uid}

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored.status == ChangeStatus.APPLIED
    assert [warning.code for warning in stored.warnings] == ["MISSING_DISPLAY_NAME"]

    mocked_change_applied_signal.assert_called_once()
    fields = mocked_change_applied_signal.call_args.kwargs["fields"]
    assert fields["uid"] == change.uid
    assert fields["person_uid"] == "local-user1"
    assert fields["target_uid"] == document.uid
    assert fields["status"] == "applied"
    assert fields["warnings"][0]["code"] == "MISSING_DISPLAY_NAME"
    mocked_change_failed_signal.assert_not_called()


@pytest.mark.asyncio
async def test_safety_guard_aborts_all_skipped_reconcile(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal,
        mocked_change_applied_signal,
        mocked_change_failed_signal) -> None:
    """
    Given a non-empty contributions list where no contribution can be applied,
    When the change is applied,
    Then a ValueError is raised, the previous contributors are kept,
        the change is FAILED and a change_failed event is emitted.
    """
    document = document_hal_article_a_persisted_model
    before = await _contributor_uids(document.uid)
    assert before

    contributions = [
        {"rank": 0, "roles": [AUT],
         "person": {"uid": None, "displayName": None, "identifiers": []},
         "affiliations": []},
    ]
    service = ChangeService()
    change = _contributions_change(document.uid, contributions,
                                   uid="sovisuplus:guard1", change_id="guard1")

    with pytest.raises(ValueError, match="aborting to avoid removing all contributors"):
        await service.create_and_apply_change(change)

    assert await _contributor_uids(document.uid) == before

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    stored = await change_dao.get_by_uid(change.uid)
    assert stored.status == ChangeStatus.FAILED
    assert "aborting to avoid removing all contributors" in stored.error_message

    mocked_change_failed_signal.assert_called_once()
    fields = mocked_change_failed_signal.call_args.kwargs["fields"]
    assert fields["uid"] == change.uid
    assert fields["status"] == "failed"
    assert "aborting" in fields["error_message"]
    mocked_change_applied_signal.assert_not_called()
    mocked_document_updated_signal.assert_not_called()


@pytest.mark.asyncio
async def test_missing_target_document_emits_failed_event_without_node(
        test_app,  # pylint: disable=unused-argument
        mocked_change_applied_signal,
        mocked_change_failed_signal) -> None:
    """
    Given a change targeting a non-existent document,
    When the change is submitted,
    Then a change_failed event is emitted and no Change node is persisted.
    """
    service = ChangeService()
    change = _contributions_change("nonexistent-document-uid", [],
                                   uid="sovisuplus:missing1", change_id="missing1")

    with pytest.raises(ValueError, match="does not exist"):
        await service.create_and_apply_change(change)

    mocked_change_failed_signal.assert_called_once()
    fields = mocked_change_failed_signal.call_args.kwargs["fields"]
    assert fields["uid"] == change.uid
    assert fields["status"] == "failed"
    assert "does not exist" in fields["error_message"]
    mocked_change_applied_signal.assert_not_called()

    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    assert await change_dao.get_by_uid(change.uid) is None


@pytest.mark.asyncio
async def test_failed_change_is_retried(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        mocked_document_updated_signal,  # pylint: disable=unused-argument
        mocked_change_applied_signal,
        mocked_change_failed_signal) -> None:
    """
    Given a change that failed on first application,
    When the same change is submitted again,
    Then it is re-applied (not skipped): the second attempt fails again here,
        producing a second change_failed event.
    """
    document = document_hal_article_a_persisted_model
    change = Change(
        uid="sovisuplus:retry1",
        target_uid=document.uid,
        target_type=TargetType.DOCUMENT,
        person_uid="local-user1",
        application="sovisuplus",
        id="retry1",
        action_type="UPDATE",
        path="documentType",
        parameters={"value": "Not_a_correct_type"},
        timestamp="2026-01-01T09:00:00Z",
    )
    service = ChangeService()

    with pytest.raises(ValueError):
        await service.create_and_apply_change(change)
    assert mocked_change_failed_signal.call_count == 1

    retried = Change.model_validate(change.model_dump() | {"status": ChangeStatus.CREATED})
    with pytest.raises(ValueError):
        await service.create_and_apply_change(retried)
    assert mocked_change_failed_signal.call_count == 2
    mocked_change_applied_signal.assert_not_called()


@pytest.mark.asyncio
async def test_batch_replay_stays_silent(
        test_app,  # pylint: disable=unused-argument
        document_hal_article_a_persisted_model: Document,
        persisted_person_a_pydantic_model: Person,
        mocked_document_updated_signal,  # pylint: disable=unused-argument
        mocked_change_applied_signal,
        mocked_change_failed_signal) -> None:
    """
    Given a stored change replayed in batch mode (after a remerge),
    When apply_changes_to_node runs,
    Then no change event is emitted toward clients.
    """
    document = document_hal_article_a_persisted_model
    internal = persisted_person_a_pydantic_model
    change = _contributions_change(
        document.uid,
        [{"rank": 0, "roles": [AUT],
          "person": {"uid": internal.uid, "displayName": internal.display_name,
                     "identifiers": []},
          "affiliations": []}],
        uid="sovisuplus:batch1", change_id="batch1")
    change_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Change)
    await change_dao.create_document_change(document, change)

    await ChangeService().apply_changes_to_node(document.uid, mode=MessageMode.BATCH)

    assert (await change_dao.get_by_uid(change.uid)).status == ChangeStatus.APPLIED
    mocked_change_applied_signal.assert_not_called()
    mocked_change_failed_signal.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_message_emits_failed_event(
        test_app,  # pylint: disable=unused-argument
        mocked_change_failed_signal) -> None:
    """
    Given a user-action message that cannot be validated into a Change (missing id),
    When the message is processed,
    Then a change_failed event is emitted with the raw correlation fields.
    """
    payload = {
        # "id" missing: Change validation fails
        "actionType": "UPDATE",
        "targetType": "DOCUMENT",
        "targetUid": "some-document-uid",
        "path": "contributions",
        "parameters": {"contributions": []},
        "personUid": "local-user1",
        "application": "sovisuplus",
        "timestamp": "2026-01-01T09:00:00Z",
    }
    processor = AMQPUserActionsMessageProcessor(asyncio.Queue(), get_app_settings())

    with pytest.raises(ValueError, match="Failed to build Change object"):
        # pylint: disable=protected-access
        await processor._process_message(
            "task.documents.document.update", json.dumps(payload).encode("utf-8"))

    mocked_change_failed_signal.assert_called_once()
    fields = mocked_change_failed_signal.call_args.kwargs["fields"]
    assert fields["person_uid"] == "local-user1"
    assert fields["target_uid"] == "some-document-uid"
    assert fields["status"] == "failed"
    assert fields["error_message"].startswith("invalid message")


def test_change_warnings_marshalling_round_trip() -> None:
    """Warnings survive a marshal/unmarshal round trip (as stored on the Change node)."""
    change = _contributions_change("doc-1", [])
    change.warnings = []
    stored = change.marshal_warnings()
    assert stored == "[]"

    change = Change.model_validate({
        **change.model_dump(exclude={"warnings"}),
        "warnings": json.dumps([{"code": "X", "message": "m", "context": {"a": 1}}]),
    })
    assert change.warnings[0].code == "X"
    assert change.warnings[0].context == {"a": 1}
