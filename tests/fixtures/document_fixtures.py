import pytest_asyncio

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.document import Document
from app.models.source_records import SourceRecord


@pytest_asyncio.fixture(name="document_persisted_model")
async def fixture_document_persisted_model(
        source_record_id_doi_1_persisted_model: SourceRecord, ) -> Document:
    """
    Persist source record Pydantic model for source_record_id_doi_1
    """
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    return document


@pytest_asyncio.fixture(name="document_hal_article_a_persisted_model")
async def fixture_document_hal_article_a_persisted_model(
        hal_article_a_source_record_persisted_model: SourceRecord) -> Document:
    """
    Persist source record Pydantic model for source_record_id_doi_1
    """
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_source_record_uid(
        hal_article_a_source_record_persisted_model.uid)
    return document


@pytest_asyncio.fixture(name="merged_hal_open_alex_persisted_model")
async def fixture_merged_hal_open_alex_persisted_model(
        hal_article_a_source_record_persisted_model: SourceRecord,
        # pylint: disable=unused-argument
        open_alex_article_b_source_record_persisted_model: SourceRecord
) -> Document:
    """
    Persist source record Pydantic model for : hal_article_a_source_record_persisted_model and
    open_alex_article_b_source_record_persisted_model
    """
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_document_by_source_record_uid(
        hal_article_a_source_record_persisted_model.uid)
    return document
