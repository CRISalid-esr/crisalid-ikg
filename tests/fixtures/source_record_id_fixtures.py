import pytest_asyncio

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.document import Document
from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService
from tests.fixtures.common import _source_record_from_json_data, _source_record_json_data_from_file


# JSON level fixtures

@pytest_asyncio.fixture(name="source_record_id_doi_1_json_data")
async def fixture_source_record_id_doi_1_json_data(_base_path) -> dict:
    """
    Create source record JSON data for source_record_id_doi_1
    """
    return _source_record_json_data_from_file(
        _base_path,
        "source_record_id_doi_1"
    )


@pytest_asyncio.fixture(name="source_record_id_doi_1_hal_1_json_data")
async def fixture_source_record_id_doi_1_hal_1_json_data(_base_path) -> dict:
    """
    Create source record JSON data for source_record_id_doi_1_hal_1
    """
    return _source_record_json_data_from_file(
        _base_path,
        "source_record_id_doi_1_hal_1"
    )


@pytest_asyncio.fixture(name="source_record_id_hal_1_json_data")
async def fixture_source_record_id_hal_1_json_data(_base_path) -> dict:
    """
    Create source record JSON data for source_record_id_hal_1
    """
    return _source_record_json_data_from_file(
        _base_path,
        "source_record_id_hal_1"
    )


# Pydantic model fixtures

@pytest_asyncio.fixture(name="source_record_id_doi_1_pydantic_model")
async def fixture_source_record_id_doi_1_pydantic_model(
        source_record_id_doi_1_json_data) -> SourceRecord:
    """
    Create source record Pydantic model for source_record_id_doi_1
    """
    return _source_record_from_json_data(source_record_id_doi_1_json_data)


@pytest_asyncio.fixture(name="source_record_id_doi_1_hal_1_pydantic_model")
async def fixture_source_record_id_doi_1_hal_1_pydantic_model(
        source_record_id_doi_1_hal_1_json_data) -> SourceRecord:
    """
    Create source record Pydantic model for source_record_id_doi_1_hal_1
    """
    return _source_record_from_json_data(source_record_id_doi_1_hal_1_json_data)


@pytest_asyncio.fixture(name="source_record_id_hal_1_pydantic_model")
async def fixture_source_record_id_hal_1_pydantic_model(
        source_record_id_hal_1_json_data) -> SourceRecord:
    """
    Create source record Pydantic model for source_record_id_hal_1
    """
    return _source_record_from_json_data(source_record_id_hal_1_json_data)


# Persisted fixtures

@pytest_asyncio.fixture(name="source_record_id_doi_1_persisted_model")
async def fixture_source_record_id_doi_1_persisted_model(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person) -> SourceRecord:
    """
    Persist source record Pydantic model for source_record_id_doi_1
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=source_record_id_doi_1_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(source_record_id_doi_1_pydantic_model.uid)


@pytest_asyncio.fixture(name="document_persisted_model")
async def fixture_document_persisted_model(
        source_record_id_doi_1_persisted_model: SourceRecord,) -> Document:
    """
    Persist source record Pydantic model for source_record_id_doi_1
    """
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    return document

@pytest_asyncio.fixture(name="source_record_id_doi_1_hal_1_persisted_model")
async def fixture_source_record_id_doi_1_hal_1_persisted_model(
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person) -> SourceRecord:
    """
    Persist source record Pydantic model for source_record_id_doi_1_hal_1
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=source_record_id_doi_1_hal_1_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(source_record_id_doi_1_hal_1_pydantic_model.uid)


@pytest_asyncio.fixture(name="source_record_id_hal_1_persisted_model")
async def fixture_source_record_id_hal_1_persisted_model(
        source_record_id_hal_1_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person) -> SourceRecord:
    """
    Persist source record Pydantic model for source_record_id_hal_1
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=source_record_id_hal_1_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(source_record_id_hal_1_pydantic_model.uid)
