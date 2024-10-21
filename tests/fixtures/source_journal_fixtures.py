import pytest_asyncio

from app.models.source_journal import SourceJournal


@pytest_asyncio.fixture(name="open_alex_source_journal_pydantic_model")
async def fixture_open_alex_source_journal_pydantic_model() -> SourceJournal:
    """
    Create a source journal pydantic model
    :return: basic source record pydantic model from ScanR data
    """
    return SourceJournal(
        source="OpenAlex",
        source_identifier="https://openalex.org/S113942516",
        issn=[
            "0007-4217",
            "2241-0104"
        ],
        eissn=["1234-5678"],
        issn_l="0007-4217",
        publisher="Example Publisher",
        titles=[
            "Sample Journal Title"
        ]

    )
