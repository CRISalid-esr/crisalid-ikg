from typing import cast
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.services.documents.crisalid_taxi_client import CrisalidTaxiClient, TaxiMatch, \
    TaxiMatchResponse
from app.services.documents.document_service import DocumentService
from app.services.source_records.equivalence_service import EquivalenceService
from app.signals import source_record_created, source_record_updated, \
    document_sources_changed, document_created_from_sources

TAXI_TOPIC_URI_A = "https://openalex.org/T11347"
TAXI_TOPIC_URI_B = "https://openalex.org/T10080"
TAXI_MODEL = "bge-m3-test"


@pytest.fixture(name="mock_taxi_client", autouse=True)
def fixture_mock_taxi_client():
    """
    Mock CrisalidTaxiClient.match so that no test ever calls the real service.
    Returns two topics (A above B) plus a subfield match for every input id.
    """

    async def mock_match(inputs: list[dict]):
        return TaxiMatchResponse(
            model=TAXI_MODEL,
            results={
                item["id"]: [
                    TaxiMatch(concept_uid=TAXI_TOPIC_URI_A, rel_type="HAS_TOPIC", value=0.91),
                    TaxiMatch(concept_uid=TAXI_TOPIC_URI_B, rel_type="HAS_TOPIC", value=0.72),
                    TaxiMatch(concept_uid="https://openalex.org/subfields/1",
                              rel_type="HAS_SUBFIELD", value=0.95),
                ]
                for item in inputs
            },
        )

    async_mock = AsyncMock(side_effect=mock_match)
    CrisalidTaxiClient.reset()
    with patch.object(CrisalidTaxiClient, "match", async_mock):
        yield async_mock
    CrisalidTaxiClient.reset()


@pytest.fixture(name="taxi_enabled_settings")
def fixture_taxi_enabled_settings():
    """
    Enable Crisalid-taxi in the cached settings for the duration of a test.
    """
    settings = get_app_settings()
    previous = (settings.taxi_enabled, settings.taxi_api_url, settings.taxi_min_input_length)
    settings.taxi_enabled = True
    settings.taxi_api_url = "http://taxi.test"
    settings.taxi_min_input_length = 10
    yield settings
    (settings.taxi_enabled, settings.taxi_api_url,
     settings.taxi_min_input_length) = previous


async def computed_document_for(source_record: SourceRecord) -> Document:
    """
    Run the equivalence step and the metadata computation for a source record,
    with Crisalid-taxi disabled, and return the resulting document.
    """
    settings = get_app_settings()
    with source_record_updated.muted(), source_record_created.muted(), \
            document_sources_changed.muted(), document_created_from_sources.muted():
        await EquivalenceService().update_source_record(None, source_record.uid)
    document_dao = cast(DocumentDAO,
                        AbstractDAOFactory().get_dao_factory("neo4j").get_dao(Document))
    document = await document_dao.get_document_by_source_record_uid(source_record.uid)
    assert document is not None
    previous = settings.taxi_enabled
    settings.taxi_enabled = False
    try:
        await DocumentService().update_from_source_records(None, document.uid)
    finally:
        settings.taxi_enabled = previous
    return await document_dao.get_document_by_uid(document.uid)


@pytest_asyncio.fixture(name="topics_document")
async def fixture_topics_document(
        source_record_id_doi_1_persisted_model: SourceRecord) -> Document:
    """
    A computed document (title "Example Article with DOI", one subject) without topics.
    """
    return await computed_document_for(source_record_id_doi_1_persisted_model)
