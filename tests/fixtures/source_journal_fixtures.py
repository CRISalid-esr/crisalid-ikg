import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.source_journal import SourceJournal


@pytest_asyncio.fixture(name="open_alex_source_journal_pydantic_model")
async def fixture_open_alex_source_journal_pydantic_model() -> SourceJournal:
    """
    Source journal pydantic model for OpenAlex
    """
    return SourceJournal(
        source="OpenAlex",
        source_identifier="https://openalex.org/S113942516",
        issn=[
            "0007-4217",  # Shared with HAL
            "2241-0104"
        ],
        eissn=["1234-5678"],
        issn_l="0007-4217",
        publisher="Example Publisher",
        titles=[
            "Sample Journal Title"
        ]
    )


@pytest_asyncio.fixture(name="hal_source_journal_pydantic_model")
async def fixture_hal_source_journal_pydantic_model() -> SourceJournal:
    """
    Source journal pydantic model for HAL, sharing ISSN with OpenAlex
    """
    return SourceJournal(
        source="HAL",
        source_identifier="hal-0123456",
        issn=["0007-4217"],  # Shared
        titles=["Another Sample Journal Title"],
        publisher="Example Publisher from HAL",
    )


@pytest_asyncio.fixture(name="scanr_source_journal_pydantic_model")
async def fixture_scanr_source_journal_pydantic_model() -> SourceJournal:
    """
    Source journal pydantic model for ScanR, sharing ISSN with OpenAlex
    """
    return SourceJournal(
        source="HAL",
        source_identifier="scanr-0123456",
        issn=["1234-5678"],  # Shared
        titles=["Another Sample Journal Title"],
        publisher="Example Publisher from ScanR",
    )


@pytest_asyncio.fixture(name="persisted_open_alex_source_journal")
async def fixture_persisted_open_alex_source_journal(
        open_alex_source_journal_pydantic_model) -> SourceJournal:
    """
    Persisted OpenAlex source journal fixture
    :param open_alex_source_journal_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    dao = factory.get_dao(SourceJournal)
    await dao.create(open_alex_source_journal_pydantic_model)
    return open_alex_source_journal_pydantic_model


@pytest_asyncio.fixture(name="persisted_hal_source_journal")
async def fixture_persisted_hal_source_journal(hal_source_journal_pydantic_model) -> SourceJournal:
    """
    Persisted HAL source journal fixture
    :param hal_source_journal_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    dao = factory.get_dao(SourceJournal)
    await dao.create(hal_source_journal_pydantic_model)
    return hal_source_journal_pydantic_model


@pytest_asyncio.fixture(name="persisted_scanr_source_journal")
async def fixture_persisted_scanr_source_journal(
        scanr_source_journal_pydantic_model) -> SourceJournal:
    """
    Persisted ScanR source journal fixture
    :param scanr_source_journal_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    dao = factory.get_dao(SourceJournal)
    await dao.create(scanr_source_journal_pydantic_model)
    return scanr_source_journal_pydantic_model
