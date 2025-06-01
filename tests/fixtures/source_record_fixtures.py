import pytest_asyncio

from app.models.people import Person
from app.models.source_records import SourceRecord
from app.services.source_records.source_record_service import SourceRecordService
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


@pytest_asyncio.fixture(name="hal_chapter_a_v2_source_record_pydantic_model")
async def fixture_hal_chapter_a_v2_source_record_pydantic_model(
        hal_chapter_a_v2_source_record_json_data) -> SourceRecord:
    """
    Create the v2 of a chapter source record pydantic model from hal data
    :return: basic source record pydantic model from hal data
    """
    return _source_record_from_json_data(hal_chapter_a_v2_source_record_json_data)


@pytest_asyncio.fixture(name="hal_chapter_a_v2_source_record_json_data")
async def fixture_hal_chapter_a_v2_source_record_json_data(_base_path) -> dict:
    """
    Create the v2 of a chapter source record dict from hal data
    :return: basic source record dict from hal data
    """
    return _source_record_json_data_from_file(_base_path, "hal_chapter_a_v2_source_record")


@pytest_asyncio.fixture(name="hal_persisted_chapter_a_source_record_pydantic_model")
async def fixture_hal_persisted_chapter_a_source_record_pydantic_model(
        hal_chapter_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from hal data
    :return: persisted source record pydantic model from hal data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=hal_chapter_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model
    )
    return await service.get_source_record(
        hal_chapter_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_chapter_a_source_record_pydantic_model")
async def fixture_hal_chapter_a_source_record_pydantic_model(
        hal_chapter_a_source_record_json_data) -> SourceRecord:
    """
    Create a chapter source record pydantic model from hal data
    :return: basic source record pydantic model from hal data
    """
    return _source_record_from_json_data(hal_chapter_a_source_record_json_data)


@pytest_asyncio.fixture(name="hal_chapter_a_source_record_json_data")
async def fixture_hal_chapter_a_source_record_json_data(_base_path) -> dict:
    """
    Create a chapter source record dict from hal data
    :return: basic source record dict from hal data
    """
    return _source_record_json_data_from_file(_base_path, "hal_chapter_a_source_record")


@pytest_asyncio.fixture(name="scanr_persisted_article_a_source_record_pydantic_model")
async def fixture_scanr_persisted_article_a_source_record_pydantic_model(
        scanr_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from ScanR data
    :return: persisted source record pydantic model from ScanR data
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_article_a_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(
        scanr_article_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="scanr_article_a_source_record_pydantic_model")
async def fixture_scanr_article_a_source_record_pydantic_model(
        scanr_article_a_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_a_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_a_source_record_json_data")
async def fixture_scanr_article_a_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_a_source_record")


@pytest_asyncio.fixture(name="scanr_article_a_source_record_with_updated_issue_pydantic_model")
async def fixture_scanr_article_a_source_record_with_updated_issue_pydantic_model(
        scanr_article_a_source_record_with_updated_issue_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_a_source_record_with_updated_issue_json_data)


@pytest_asyncio.fixture(name="scanr_article_a_source_record_with_updated_issue_json_data")
async def fixture_scanr_article_a_source_record_with_updated_issue_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "scanr_article_a_source_record_with_updated_issue"
    )


@pytest_asyncio.fixture(name="scanr_persisted_article_a_v2_source_record_pydantic_model")
async def fixture_scanr_persisted_article_a_v2_source_record_pydantic_model(
        scanr_article_a_v2_source_record_pydantic_model: SourceRecord,
        persisted_person_b_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from ScanR data
    :return: persisted source record pydantic model from ScanR data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=scanr_article_a_v2_source_record_pydantic_model,
        harvested_for=persisted_person_b_pydantic_model)
    return await service.get_source_record(
        scanr_article_a_v2_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="scanr_article_a_v2_source_record_pydantic_model")
async def fixture_scanr_article_a_v2_source_record_pydantic_model(
        scanr_article_a_v2_source_record_json_data) -> SourceRecord:
    """
    Create the v2 of an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_a_v2_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_a_v2_source_record_json_data")
async def fixture_scanr_article_a_v2_source_record_json_data(_base_path) -> dict:
    """
    Create the v2 of an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_a_v2_source_record")


@pytest_asyncio.fixture(name="article_exoplanet_from_oa_source_record_pydantic_model")
async def fixture_article_exoplanet_from_oa_source_record_pydantic_model(
        article_exoplanet_from_oa_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from OpenAire data
    :return: basic source record pydantic model from OpenAire data
    """
    return _source_record_from_json_data(article_exoplanet_from_oa_source_record_json_data)


@pytest_asyncio.fixture(name="article_exoplanet_from_oa_source_record_json_data")
async def fixture_article_exoplanet_from_oa_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from OpenAire data
    :return: basic source record dict from OpenAire data
    """
    return _source_record_json_data_from_file(_base_path,
                                              "contributors/article_exoplanet_from_oa")


@pytest_asyncio.fixture(name="article_exoplanet_from_scanr_source_record_pydantic_model")
async def fixture_article_exoplanet_from_scanr_source_record_pydantic_model(
        article_exoplanet_from_scanr_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(article_exoplanet_from_scanr_source_record_json_data)


@pytest_asyncio.fixture(name="article_exoplanet_from_scanr_source_record_json_data")
async def fixture_article_exoplanet_from_scanr_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path,
                                              "contributors/article_exoplanet_from_scanr")


@pytest_asyncio.fixture(
    name="scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model")
async def fixture_scanr_article_a_v2_source_record_without_hal_doi_identifiers_pydantic_model(
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_json_data) -> SourceRecord:
    """
    Create the v2 of an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(
        scanr_article_a_v2_source_record_without_hal_doi_identifiers_json_data)


@pytest_asyncio.fixture(
    name="scanr_article_a_v2_source_record_without_hal_doi_identifiers_json_data")
async def fixture_scanr_article_a_v2_source_record_without_hal_doi_identifiers_json_data(
        _base_path) -> dict:
    """
    Create the v2 of an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "scanr_article_a_v2_source_record_without_hal_doi_identifiers"
    )


@pytest_asyncio.fixture(name="scanr_article_a_v3_source_record_pydantic_model")
async def fixture_scanr_article_a_v3_source_record_pydantic_model(
        scanr_article_a_v3_source_record_json_data) -> SourceRecord:
    """
    Create the v3 of an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_a_v3_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_a_v3_source_record_json_data")
async def fixture_scanr_article_a_v3_source_record_json_data(_base_path) -> dict:
    """
    Create the v3 of an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_a_v3_source_record")


@pytest_asyncio.fixture(name="scanr_article_b_source_record_pydantic_model")
async def fixture_scanr_article_b_source_record_pydantic_model(
        scanr_article_b_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_b_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_b_source_record_json_data")
async def fixture_scanr_article_b_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_b_source_record")


@pytest_asyncio.fixture(name="scanr_persisted_article_c_source_record_pydantic_model")
async def fixture_scanr_persisted_article_c_source_record_pydantic_model(
        scanr_article_c_source_record_pydantic_model: SourceRecord,
        persisted_person_b_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from ScanR data
    :return: persisted source record pydantic model from ScanR data
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=scanr_article_c_source_record_pydantic_model,
                                       harvested_for=persisted_person_b_pydantic_model)
    return await service.get_source_record(
        scanr_article_c_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="scanr_article_c_source_record_pydantic_model")
async def fixture_scanr_article_c_source_record_pydantic_model(
        scanr_article_c_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_c_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_c_source_record_json_data")
async def fixture_scanr_article_c_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_c_source_record")


@pytest_asyncio.fixture(name="scanr_article_c_v2_source_record_pydantic_model")
async def fixture_scanr_article_c_v2_source_record_pydantic_model(
        scanr_article_c_v2_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from ScanR data
    :return: basic source record pydantic model from ScanR data
    """
    return _source_record_from_json_data(scanr_article_c_v2_source_record_json_data)


@pytest_asyncio.fixture(name="scanr_article_c_v2_source_record_json_data")
async def fixture_scanr_article_c_v2_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from ScanR data
    :return: basic source record dict from ScanR data
    """
    return _source_record_json_data_from_file(_base_path, "scanr_article_c_v2_source_record")


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


@pytest_asyncio.fixture(name="idref_record_with_person_a_as_contributor_pydantic_model")
async def fixture_idref_record_with_person_a_as_contributor_pydantic_model(
        idref_record_with_person_a_as_contributor_json_data) -> SourceRecord:
    """
    Create a basic source record pydantic model from IdRef data
    :return: basic source record pydantic model from IdRef data
    """
    return _source_record_from_json_data(idref_record_with_person_a_as_contributor_json_data)


@pytest_asyncio.fixture(name="idref_record_with_person_a_as_contributor_json_data")
async def fixture_idref_record_with_person_a_as_contributor_json_data(_base_path) -> dict:
    """
    Create a source record dict from IdRef data
    :return: source record dict from IdRef data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "idref_record_with_person_a_as_contributor"
    )


@pytest_asyncio.fixture(name="scanr_record_with_person_a_as_contributor_pydantic_model")
async def fixture_scanr_record_with_person_a_as_contributor_pydantic_model(
        scanr_record_with_person_a_as_contributor_json_data) -> SourceRecord:
    """
    Create a source record pydantic model from IdRef data
    :return: source record pydantic model from IdRef data
    """
    return _source_record_from_json_data(scanr_record_with_person_a_as_contributor_json_data)


@pytest_asyncio.fixture(name="scanr_record_with_person_a_as_contributor_json_data")
async def fixture_scanr_record_with_person_a_as_contributor_json_data(_base_path) -> dict:
    """
    Create a source record dict from scanr data
    :return: source record dict from scanr data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "scanr_record_with_person_a_as_contributor"
    )


@pytest_asyncio.fixture(
    name="scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model")
async def \
        fixture_scanr_record_with_person_a_as_contrib_and_additional_alt_labels_pyd_model(
        scanr_record_with_person_a_as_contributor_and_additional_alt_labels_json_data
) -> SourceRecord:
    """
    Create a source record pydantic model from IdRef data
    :return: source record pydantic model from IdRef data
    """
    return _source_record_from_json_data(
        scanr_record_with_person_a_as_contributor_and_additional_alt_labels_json_data
    )


@pytest_asyncio.fixture(
    name="scanr_record_with_person_a_as_contributor_and_additional_alt_labels_json_data")
async def fixture_scanr_record_with_person_a_as_contributor_and_additional_alt_labels_json_data(
        _base_path) -> dict:
    """
    Create a source record dict from scanr data
    :return: source record dict from scanr data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "scanr_record_with_person_a_as_contributor_and_additional_alt_labels"
    )


@pytest_asyncio.fixture(name="scanr_record_with_person_b_as_contributor_pydantic_model")
async def fixture_scanr_record_with_person_b_as_contributor_pydantic_model(
        scanr_record_with_person_b_as_contributor_json_data) -> SourceRecord:
    """
    Create a source record pydantic model from IdRef data
    :return: source record pydantic model from IdRef data
    """
    return _source_record_from_json_data(scanr_record_with_person_b_as_contributor_json_data)


@pytest_asyncio.fixture(name="scanr_record_with_person_b_as_contributor_json_data")
async def fixture_scanr_record_with_person_b_as_contributor_json_data(_base_path) -> dict:
    """
    Create a source record dict from scanr data
    :return: source record dict from scanr data
    """
    return _source_record_json_data_from_file(
        _base_path,
        "scanr_record_with_person_b_as_contributor"
    )


@pytest_asyncio.fixture(name="source_record_without_title_json_data")
async def fixture_source_record_without_title_record_json_data(_base_path) -> dict:
    """
    Create an invalid source record without title
    :return: invalid source record dict without title
    """
    return _source_record_json_data_from_file(_base_path, "source_record_without_title")


@pytest_asyncio.fixture(name="open_alex_article_source_record_with_issue_title_pydantic_model")
async def fixture_open_alex_article_source_record_with_issue_title_pydantic_model(
        open_alex_article_source_record_with_issue_title_json_data) -> SourceRecord:
    """
    Create a basic source record pydantic model from OpenAlex data
    :return: basic source record pydantic model from OpenAlex data
    """
    return _source_record_from_json_data(open_alex_article_source_record_with_issue_title_json_data)


@pytest_asyncio.fixture(name="open_alex_article_source_record_with_issue_title_json_data")
async def fixture_open_alex_article_source_record_with_issue_title_json_data(_base_path) -> dict:
    """
    Create a thesis source record dict from OpenAlex data
    :return: basic source record dict from OpenAlex data
    """
    return _source_record_json_data_from_file(_base_path,
                                              "open_alex_article_source_record_with_issue_title")


@pytest_asyncio.fixture(name="source_record_with_unknown_source_json_data")
async def fixture_source_record_with_unknown_source_json_data(_base_path) -> dict:
    """
    Create a source record with an unknown source
    :return:  record from an unknown source
    """
    return _source_record_json_data_from_file(_base_path, "source_record_with_unknown_source")


@pytest_asyncio.fixture(name="hal_persisted_article_a_source_record_pydantic_model")
async def fixture_hal_persisted_article_a_source_record_pydantic_model(
        hal_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from hal data
    :return: persisted source record pydantic model from hal data
    """
    service = SourceRecordService()
    await service.create_source_record(source_record=hal_article_a_source_record_pydantic_model,
                                       harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(
        hal_article_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_article_a_source_record_persisted_model")
async def fixture_hal_article_a_source_record_persisted_model(
        hal_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_d_pydantic_model: Person) -> SourceRecord:
    """
    Persist a source record pydantic model from hal data
    :return: persisted source record pydantic model from hal data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=hal_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_d_pydantic_model
    )
    return await service.get_source_record(
        hal_article_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_article_a_source_record_pydantic_model")
async def fixture_hal_article_a_source_record_pydantic_model(
        hal_article_a_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from hal data
    :return: basic source record pydantic model from hal data
    """
    return _source_record_from_json_data(hal_article_a_source_record_json_data)


@pytest_asyncio.fixture(name="hal_article_a_source_record_json_data")
async def fixture_hal_article_a_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from hal data
    :return: basic source record dict from hal data
    """
    return _source_record_json_data_from_file(_base_path, "hal_article_a_source_record")


@pytest_asyncio.fixture(name="open_alex_persisted_article_a_source_record_pydantic_model")
async def fixture_open_alex_persisted_article_a_source_record_pydantic_model(
        open_alex_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from open_alex data
    :return: persisted source record pydantic model from open_alex data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=open_alex_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model
    )
    return await service.get_source_record(
        open_alex_article_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="open_alex_article_a_source_record_pydantic_model")
async def fixture_open_alex_article_a_source_record_pydantic_model(
        open_alex_article_a_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from open_alex data
    :return: basic source record pydantic model from open_alex data
    """
    return _source_record_from_json_data(open_alex_article_a_source_record_json_data)


@pytest_asyncio.fixture(name="open_alex_article_a_source_record_json_data")
async def fixture_open_alex_article_a_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from open_alex data
    :return: basic source record dict from open_alex data
    """
    return _source_record_json_data_from_file(_base_path, "open_alex_article_a_source_record")


@pytest_asyncio.fixture(name="open_alex_article_b_source_record_pydantic_model")
async def fixture_open_alex_article_b_source_record_pydantic_model(
        open_alex_article_b_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from open_alex data
    :return: basic source record pydantic model from open_alex data
    """
    return _source_record_from_json_data(open_alex_article_b_source_record_json_data)


@pytest_asyncio.fixture(name="open_alex_article_b_source_record_json_data")
async def fixture_open_alex_article_b_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from open_alex data
    :return: basic source record dict from open_alex data
    """
    return _source_record_json_data_from_file(_base_path, "open_alex_article_b_source_record")


@pytest_asyncio.fixture(name="idref_persisted_article_a_source_record_pydantic_model")
async def fixture_idref_persisted_article_a_source_record_pydantic_model(
        idref_article_a_source_record_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from open_alex data
    :return: persisted source record pydantic model from open_alex data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=idref_article_a_source_record_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model
    )
    return await service.get_source_record(
        idref_article_a_source_record_pydantic_model.uid)


@pytest_asyncio.fixture(name="idref_article_a_source_record_pydantic_model")
async def fixture_idref_article_a_source_record_pydantic_model(
        idref_article_a_source_record_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from open_alex data
    :return: basic source record pydantic model from open_alex data
    """
    return _source_record_from_json_data(idref_article_a_source_record_json_data)


@pytest_asyncio.fixture(name="idref_article_a_source_record_json_data")
async def fixture_idref_article_a_source_record_json_data(_base_path) -> dict:
    """
    Create an article source record dict from open_alex data
    :return: basic source record dict from open_alex data
    """
    return _source_record_json_data_from_file(_base_path, "idref_article_a_source_record")


@pytest_asyncio.fixture(name="hal_persisted_article_source_record_pydantic_model")
async def fixture_hal_persisted_article_source_record_with_custom_metadata_pydantic_model(
        hal_article_source_record_with_custom_metadata_pydantic_model: SourceRecord,
        persisted_person_a_pydantic_model: Person
) -> SourceRecord:
    """
    Persist a source record pydantic model from ScanR data
    :return: persisted source record pydantic model from ScanR data
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=hal_article_source_record_with_custom_metadata_pydantic_model,
        harvested_for=persisted_person_a_pydantic_model)
    return await service.get_source_record(
        hal_article_source_record_with_custom_metadata_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_article_source_record_with_custom_metadata_pydantic_model")
async def fixture_hal_article_source_record_with_custom_metadata_pydantic_model(
        hal_article_source_record_with_custom_metadata_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from open_alex data
    :return: basic source record pydantic model from open_alex data
    """
    return _source_record_from_json_data(hal_article_source_record_with_custom_metadata_json_data)


@pytest_asyncio.fixture(name="hal_article_source_record_with_custom_metadata_json_data")
async def fixture_hal_article_source_record_with_custom_metadata_json_data(_base_path) -> dict:
    """
    Create an article source record dict from open_alex data
    :return: basic source record dict from open_alex data
    """
    return _source_record_json_data_from_file(_base_path,
                                              "hal_article_source_record_with_custom_metadata")


@pytest_asyncio.fixture(name="hal_article_source_record_with_custom_metadata_v2_pydantic_model")
async def fixture_hal_article_source_record_with_custom_metadata_v2_pydantic_model(
        hal_article_source_record_with_custom_metadata_v2_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from open_alex data
    :return: basic source record pydantic model from open_alex data
    """
    return _source_record_from_json_data(
        hal_article_source_record_with_custom_metadata_v2_json_data)


@pytest_asyncio.fixture(name="hal_article_source_record_with_custom_metadata_v2_json_data")
async def fixture_hal_article_source_record_with_custom_metadata_v2_json_data(_base_path) -> dict:
    """
    Create an article source record dict from open_alex data
    :return: basic source record dict from open_alex data
    """
    return _source_record_json_data_from_file(_base_path,
                                              "hal_article_source_record_with_custom_metadata_v2")


@pytest_asyncio.fixture(name="open_alex_article_with_journal_1_persisted_model")
async def fixture_open_alex_article_with_journal_1_persisted_model(
        open_alex_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person) -> SourceRecord:
    """
    Persist a source record pydantic model from OpenAlex data with journal 1 information
    :param open_alex_article_with_journal_1_pydantic_model:
    :param persisted_person_f_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=open_alex_article_with_journal_1_pydantic_model,
        harvested_for=persisted_person_f_pydantic_model
    )
    return await service.get_source_record(
        open_alex_article_with_journal_1_pydantic_model.uid)


@pytest_asyncio.fixture(name="open_alex_article_with_journal_1_pydantic_model")
async def fixture_open_alex_article_with_journal_1_pydantic_model(
        open_alex_article_with_journal_1_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from OpenAlex data with journal 1 information
    :param open_alex_article_with_journal_1_json_data:
    :return:
    """
    return _source_record_from_json_data(open_alex_article_with_journal_1_json_data)


@pytest_asyncio.fixture(name="open_alex_article_with_journal_1_json_data")
async def fixture_open_alex_article_with_journal_1_json_data(_base_path) -> dict:
    """
    Create an article source record dict from OpenAlex data with journal 1 information
    :param _base_path:
    :return:
    """
    return _source_record_json_data_from_file(_base_path, "open_alex_article_with_journal_1")


@pytest_asyncio.fixture(name="open_alex_article_with_journal_2_persisted_model")
async def fixture_open_alex_article_with_journal_2_persisted_model(
        open_alex_article_with_journal_2_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person) -> SourceRecord:
    """
    Persist a source record pydantic model from OpenAlex data with journal 2 information
    :param open_alex_article_with_journal_2_pydantic_model:
    :param persisted_person_f_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=open_alex_article_with_journal_2_pydantic_model,
        harvested_for=persisted_person_f_pydantic_model
    )
    return await service.get_source_record(
        open_alex_article_with_journal_2_pydantic_model.uid)


@pytest_asyncio.fixture(name="open_alex_article_with_journal_2_pydantic_model")
async def fixture_open_alex_article_with_journal_2_pydantic_model(
        open_alex_article_with_journal_2_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from OpenAlex data with journal 2 information
    :param open_alex_article_with_journal_2_json_data:
    :return:
    """
    return _source_record_from_json_data(open_alex_article_with_journal_2_json_data)


@pytest_asyncio.fixture(name="open_alex_article_with_journal_2_json_data")
async def fixture_open_alex_article_with_journal_2_json_data(_base_path) -> dict:
    """
    Create an article source record dict from OpenAlex data with journal 2 information
    :param _base_path:
    :return:
    """
    return _source_record_json_data_from_file(_base_path, "open_alex_article_with_journal_2")


@pytest_asyncio.fixture(name="hal_article_with_journal_1_persisted_model")
async def fixture_hal_article_with_journal_1_persisted_model(
        hal_article_with_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person) -> SourceRecord:
    """
    Persist a source record pydantic model from HAL data with journal 1 information
    :param hal_article_with_journal_1_pydantic_model:
    :param persisted_person_f_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=hal_article_with_journal_1_pydantic_model,
        harvested_for=persisted_person_f_pydantic_model
    )
    return await service.get_source_record(
        hal_article_with_journal_1_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_article_with_journal_1_pydantic_model")
async def fixture_hal_article_with_journal_1_pydantic_model(
        hal_article_with_journal_1_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from HAL data with journal 1 information
    :param hal_article_with_journal_1_json_data:
    :return:
    """
    return _source_record_from_json_data(hal_article_with_journal_1_json_data)


@pytest_asyncio.fixture(name="hal_article_with_journal_1_json_data")
async def fixture_hal_article_with_journal_1_json_data(_base_path) -> dict:
    """
    Create an article source record dict from HAL data with journal 1 information
    :param _base_path:
    :return:
    """
    return _source_record_json_data_from_file(_base_path, "hal_article_with_journal_1")


@pytest_asyncio.fixture(name="hal_article_with_journal_2_pydantic_model")
async def fixture_hal_article_with_journal_2_pydantic_model(
        hal_article_with_journal_2_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from HAL data with journal 2 information
    :param hal_article_with_journal_2_json_data:
    :return:
    """
    return _source_record_from_json_data(hal_article_with_journal_2_json_data)


@pytest_asyncio.fixture(name="hal_article_with_journal_2_json_data")
async def fixture_hal_article_with_journal_2_json_data(_base_path) -> dict:
    """
    Create an article source record dict from HAL data with journal 2 information
    :param _base_path:
    :return:
    """
    return _source_record_json_data_from_file(_base_path, "hal_article_with_journal_2")


@pytest_asyncio.fixture(name="hal_article_with_inconsistent_journal_1_persisted_model")
async def fixture_hal_article_with_inconsistent_journal_1_persisted_model(
        hal_article_with_inconsistent_journal_1_pydantic_model: SourceRecord,
        persisted_person_f_pydantic_model: Person) -> SourceRecord:
    """
    Persist a source record pydantic model from HAL data with inconsistent journal 1 information
    :param hal_article_with_inconsistent_journal_1_pydantic_model:
    :param persisted_person_f_pydantic_model:
    :return:
    """
    service = SourceRecordService()
    await service.create_source_record(
        source_record=hal_article_with_inconsistent_journal_1_pydantic_model,
        harvested_for=persisted_person_f_pydantic_model
    )
    return await service.get_source_record(
        hal_article_with_inconsistent_journal_1_pydantic_model.uid)


@pytest_asyncio.fixture(name="hal_article_with_inconsistent_journal_1_pydantic_model")
async def fixture_hal_article_with_inconsistent_journal_1_pydantic_model(
        hal_article_with_inconsistent_journal_1_json_data) -> SourceRecord:
    """
    Create an article source record pydantic model from HAL data
    with inconsistent journal 1 information
    :param hal_article_with_inconsistent_journal_1_json_data:
    :return:
    """
    return _source_record_from_json_data(hal_article_with_inconsistent_journal_1_json_data)


@pytest_asyncio.fixture(name="hal_article_with_inconsistent_journal_1_json_data")
async def fixture_hal_article_with_inconsistent_journal_1_json_data(_base_path) -> dict:
    """
    Create an article source record dict from HAL data with inconsistent journal 1 information
    :param _base_path:
    :return:
    """
    return _source_record_json_data_from_file(_base_path, "hal_article_with_inconsistent_journal_1")
