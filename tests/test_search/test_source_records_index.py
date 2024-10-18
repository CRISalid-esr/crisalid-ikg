from unittest import mock

import pytest

from app.models.people import Person
from app.models.source_records import SourceRecord
from app.search.source_record_index import SourceRecordIndex
from app.services.source_records.source_record_service import SourceRecordService


@pytest.fixture(name="mock_source_record_index_add_source_record", autouse=True)
def fixture_mock_source_record_index_add_source_record():
    """Mock the async add_source_record method of SourceRecordIndex"""
    with mock.patch.object(SourceRecordIndex, "add_source_record",
                           new=mock.AsyncMock()) as mock_add_source_record:
        yield mock_add_source_record


async def test_signal_source_record_created(
        test_app,  # pylint: disable=unused-argument
        persisted_person_a_pydantic_model: Person,
        scanr_thesis_source_record_pydantic_model: SourceRecord,
        mock_source_record_index_add_source_record: mock.MagicMock):
    """
    Given a new source record Pydantic model
    When the source record is added to the graph
    Then the source record index add_source_record method is called
    :param test_app: juste to ensure bliker initialization (through CrisalidIKG constructor)
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=scanr_thesis_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model
    )
    mock_source_record_index_add_source_record.assert_called_once_with(
        service,
        source_record_id='ScanR-nnt2023xyz135'
    )
