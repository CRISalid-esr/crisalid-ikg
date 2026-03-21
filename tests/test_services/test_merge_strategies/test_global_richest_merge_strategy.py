from app.models.journal_article import JournalArticle
from app.models.source_records import SourceRecord
from app.services.documents.merge_strategies.global_richest_merge_strategy import \
    GlobalRichestMergeStrategy


async def test_merge_uses_harvester_order_as_fallback(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
) -> None:
    """
    When records have equal scores, the strategy harvester order must be used
    as a fallback.
    """
    strategy = GlobalRichestMergeStrategy(
        source_records=[
            source_record_id_doi_1_pydantic_model,  # scanr
            source_record_id_hal_1_pydantic_model,  # hal
        ],
        parameters={
            "titles": 0,
            "abstracts": 0,
            "contributions": 0,
            "subjects": 0,
            "issued": 0,
        },
        document_type=JournalArticle,
        harvesters=["hal", "scanr"],
    )

    document = strategy.merge()

    assert document is not None
    assert document.titles == source_record_id_hal_1_pydantic_model.titles
    assert document.publication_date == source_record_id_hal_1_pydantic_model.raw_issued


async def test_merge_excludes_harvesters_not_in_strategy_list(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
) -> None:
    """
    Harvesters missing from the strategy harvester list must be excluded
    from the merge.
    """
    strategy = GlobalRichestMergeStrategy(
        source_records=[
            source_record_id_doi_1_pydantic_model,  # scanr
            source_record_id_hal_1_pydantic_model,  # hal
        ],
        parameters={
            "titles": 1,
            "abstracts": 1,
            "contributions": 1,
            "subjects": 1,
            "issued": 1,
        },
        document_type=JournalArticle,
        harvesters=["hal"],
    )

    document = strategy.merge()

    assert document is not None
    assert strategy.source_records == [source_record_id_hal_1_pydantic_model]
    assert document.titles == source_record_id_hal_1_pydantic_model.titles
    assert document.publication_date == source_record_id_hal_1_pydantic_model.raw_issued
    assert document.subjects == source_record_id_hal_1_pydantic_model.subjects


async def test_merge_prefers_higher_score_before_harvester_order(
        source_record_id_doi_1_hal_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
) -> None:
    """
    Higher score must win before harvester ordering is considered.
    """
    strategy = GlobalRichestMergeStrategy(
        source_records=[
            source_record_id_doi_1_hal_1_pydantic_model,  # scanr
            source_record_id_hal_1_pydantic_model,  # hal
        ],
        parameters={
            "titles": 1,
            "abstracts": 0,
            "contributions": 0,
            "subjects": 0,
            "issued": 0,
        },
        document_type=JournalArticle,
        harvesters=["hal", "scanr"],
    )

    document = strategy.merge()

    assert document is not None
    assert document.titles == source_record_id_doi_1_hal_1_pydantic_model.titles


async def test_merge_returns_empty_document_when_all_records_are_excluded(
        source_record_id_doi_1_pydantic_model: SourceRecord,
        source_record_id_hal_1_pydantic_model: SourceRecord,
) -> None:
    """
    If no source record harvester is allowed by the strategy, the merge should
    still return an empty document instance.
    """
    strategy = GlobalRichestMergeStrategy(
        source_records=[
            source_record_id_doi_1_pydantic_model,  # scanr
            source_record_id_hal_1_pydantic_model,  # hal
        ],
        parameters={
            "titles": 1,
            "abstracts": 1,
            "contributions": 1,
            "subjects": 1,
            "issued": 1,
        },
        document_type=JournalArticle,
        harvesters=["idref"],
    )

    document = strategy.merge()

    assert document is not None
    assert isinstance(document, JournalArticle)
    assert strategy.source_records == []
    assert document.titles == []
    assert document.abstracts == []
    assert document.subjects == []
    assert document.publication_date is None
   