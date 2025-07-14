import pytest

from app.models.change import Change, TargetType, ChangeStatus
from app.services.changes.change_processor_factory import ChangeProcessorFactory
from app.services.changes.processors.document_subjects_change_processor import (
    DocumentSubjectsChangeProcessor,
)


@pytest.mark.asyncio
async def test_get_document_subjects_change_processor():
    """
    Test that the ChangeProcessorFactory returns the correct processor
    for a document subjects change.
    :return:
    """
    change = Change(
        uid="test:001",
        targetUid="doc-123",
        targetType=TargetType.DOCUMENT,
        personUid="person-456",
        application="test",
        id="001",
        action="REMOVE",
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
