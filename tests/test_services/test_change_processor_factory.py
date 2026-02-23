# file: tests/test_services/test_change_processor_factory.py
import pytest

from app.models.change import Change, TargetType, ChangeStatus
from app.services.changes.change_processor_factory import ChangeProcessorFactory
from app.services.changes.processors.document_merge_change_processor import \
    DocumentMergeChangeProcessor
from app.services.changes.processors.document_subjects_change_processor import (
    DocumentSubjectsChangeProcessor,
)


@pytest.mark.asyncio
async def test_get_document_subjects_change_processor():
    """
    The factory should return DocumentSubjectsChangeProcessor for a DOCUMENT/subjects change.
    """
    change = Change(
        uid="test:001",
        targetUid="doc-123",
        targetType=TargetType.DOCUMENT,
        personUid="person-456",
        application="test",
        id="001",
        action_type="REMOVE",
        path="subjects",
        parameters={"conceptUids": ["concept-789"]},
        timestamp="2025-07-13T12:00:00Z",
        status=ChangeStatus.CREATED,
    )

    processor = ChangeProcessorFactory.get_processor(change)

    assert isinstance(processor, DocumentSubjectsChangeProcessor)
    assert processor.change.uid == "test:001"
    assert processor.change.path == "subjects"
    assert processor.change.target_type == TargetType.DOCUMENT

@pytest.mark.asyncio
async def test_get_document_merge_change_processor():
    """
    The factory should return DocumentMergeChangeProcessor for a DOCUMENT/MERGE change.
    """
    change = Change(
        uid="test:merge:001",
        targetUid="78ee9888-1856-42d7-b48d-a0fad2bd7835",
        targetType=TargetType.DOCUMENT,
        personUid="local-jdupont",
        application="sovisuplus",
        id="9bf2ec49-8ae5-404a-88db-a50c6b3cd144",
        action_type="MERGE",  # <- key routing signal
        path=None,  # MERGE messages carry no path
        parameters={"mergedDocumentUids": ["57237b4d-7de8-4762-abf9-18e54ba2a592"]},
        timestamp="2025-09-28T01:52:40.218Z",
        status=ChangeStatus.CREATED,
    )

    processor = ChangeProcessorFactory.get_processor(change)

    assert isinstance(processor, DocumentMergeChangeProcessor)
    assert processor.change.action_type == "MERGE"
    assert processor.change.target_type == TargetType.DOCUMENT
    assert processor.change.parameters["mergedDocumentUids"] == [
        "57237b4d-7de8-4762-abf9-18e54ba2a592"
    ]
