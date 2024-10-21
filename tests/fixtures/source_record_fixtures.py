import pytest_asyncio

from app.models.people import Person
from app.models.source_records import SourceRecord
from tests.fixtures.common import _source_record_from_json_data, \
    _source_record_json_data_from_file


@pytest_asyncio.fixture(name="scanr_thesis_source_record_pydantic_model")
async def fixture_scanr_thesis_source_record_pydantic_model(
        scanr_thesis_source_record_json_data) -> Person:
    """
    Create a thesis source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_thesis_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_thesis_source_record_json_data")
async def fixture_scanr_thesis_source_record_json_data(_base_path) -> dict:
    """
    Create a thesis source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_thesis_source_record")


@pytest_asyncio.fixture(name="idref_thesis_source_record_pydantic_model")
async def fixture_idref_thesis_source_record_pydantic_model(
        idref_thesis_source_record_json_data) -> SourceRecord:
    """
    Create a basic source record pydantic model from IdRef data
    :return: basic source record pydantic model from IdRef data
    """
    return _source_record_from_json_data(idref_thesis_source_record_json_data)


@pytest_asyncio.fixture(name="idref_thesis_source_record_json_data")
async def fixture_idref_thesis_source_record_json_data(_base_path) -> dict:
    """
    Create a thesis source record dict from IdRef data
    :return: basic source record dict from IdRef data
    """
    return _source_record_json_data_from_file(_base_path, "idref_thesis_source_record")


@pytest_asyncio.fixture(name="open_alex_article_source_record_pydantic_model")
async def fixture_open_alex_article_source_record_pydantic_model(
        open_alex_article_source_record_json_data) -> SourceRecord:
    """
    Create a basic source record pydantic model from OpenAlex data
    :return: basic source record pydantic model from OpenAlex data
    """
    return _source_record_from_json_data(open_alex_article_source_record_json_data)


@pytest_asyncio.fixture(name="open_alex_article_source_record_json_data")
async def fixture_open_alex_article_source_record_json_data(_base_path) -> dict:
    """
    Create a thesis source record dict from OpenAlex data
    :return: basic source record dict from OpenAlex data
    """
    return _source_record_json_data_from_file(_base_path, "open_alex_article_source_record")
