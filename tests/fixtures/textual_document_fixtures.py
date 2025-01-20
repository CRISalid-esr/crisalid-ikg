import pytest_asyncio

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.document import Document
from app.models.source_records import SourceRecord


@pytest_asyncio.fixture(name="textual_document_persisted_model")
async def fixture_textual_document_persisted_model(
        source_record_id_doi_1_persisted_model: SourceRecord, ) -> Document:
    """
    Persist source record Pydantic model for source_record_id_doi_1
    """
    document_dao = AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document)
    document = await document_dao.get_textual_document_by_source_record_uid(
        source_record_id_doi_1_persisted_model.uid)
    return document
