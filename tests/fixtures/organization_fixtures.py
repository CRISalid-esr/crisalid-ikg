import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.organization_unit import OrganizationBase
from tests.fixtures.common import _organization_json_data_from_file, \
    _organization_unit_json_data_from_file, _organization_unit_from_json_data


@pytest_asyncio.fixture(name="research_unit_a_pydantic_model")
async def fixture_research_unit_a_pydantic_model(research_unit_a_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(research_unit_a_json_data)


@pytest_asyncio.fixture(name="research_unit_a_json_data")
async def fixture_research_unit_a_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "research_unit_a")


@pytest_asyncio.fixture(name="persisted_research_unit_a_pydantic_model")
async def fixture_persisted_research_unit_a_pydantic_model(
        research_unit_a_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(research_unit_a_pydantic_model)
    return research_unit_a_pydantic_model


@pytest_asyncio.fixture(name="research_unit_b_pydantic_model")
async def fixture_research_unit_b_pydantic_model(research_unit_b_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(research_unit_b_json_data)


@pytest_asyncio.fixture(name="research_unit_b_json_data")
async def fixture_research_unit_b_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "research_unit_b")


@pytest_asyncio.fixture(name="persisted_research_unit_b_pydantic_model")
async def fixture_persisted_research_unit_b_pydantic_model(
        research_unit_b_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(research_unit_b_pydantic_model)
    return research_unit_b_pydantic_model


@pytest_asyncio.fixture(
    name="research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_pydantic_model")
async def fixture_research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_pydantic_model(
        research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_json_data
) -> OrganizationBase:
    return _organization_unit_from_json_data(
        research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_json_data)


@pytest_asyncio.fixture(
    name="research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_json_data")
async def fixture_research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added_json_data(
        _base_path) -> dict:
    return _organization_unit_json_data_from_file(
        _base_path,
        "research_unit_a_with_nam_acr_desc_str_ror_ital_desc_name_added")


@pytest_asyncio.fixture(name="research_unit_a_with_invalid_identifier_type_json_data")
async def fixture_research_unit_a_with_invalid_identifier_type_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path,
                                                  "research_unit_a_with_invalid_identifier_type")


@pytest_asyncio.fixture(name="research_unit_b_without_name_json_data")
async def fixture_research_unit_b_without_name_json_data(_base_path) -> dict:
    return _organization_json_data_from_file(_base_path, "research_unit_b_without_name")


@pytest_asyncio.fixture(name="research_unit_with_duplicate_identifiers_json_data")
async def fixture_research_unit_with_duplicate_identifiers_json_data(_base_path) -> dict:
    return _organization_json_data_from_file(_base_path, "research_unit_with_duplicate_identifiers")


# ── New organization unit fixtures ────────────────────────────────────────────

@pytest_asyncio.fixture(name="institution_a_json_data")
async def fixture_institution_a_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "institution_a")


@pytest_asyncio.fixture(name="institution_a_pydantic_model")
async def fixture_institution_a_pydantic_model(institution_a_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(institution_a_json_data)


@pytest_asyncio.fixture(name="persisted_institution_a_pydantic_model")
async def fixture_persisted_institution_a_pydantic_model(
        institution_a_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(institution_a_pydantic_model)
    return institution_a_pydantic_model


@pytest_asyncio.fixture(name="institution_subdivision_a_json_data")
async def fixture_institution_subdivision_a_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "institution_subdivision_a")


@pytest_asyncio.fixture(name="institution_subdivision_a_pydantic_model")
async def fixture_institution_subdivision_a_pydantic_model(
        institution_subdivision_a_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(institution_subdivision_a_json_data)


@pytest_asyncio.fixture(name="persisted_institution_subdivision_a_pydantic_model")
async def fixture_persisted_institution_subdivision_a_pydantic_model(
        institution_subdivision_a_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(institution_subdivision_a_pydantic_model)
    return institution_subdivision_a_pydantic_model


@pytest_asyncio.fixture(name="research_unit_center_json_data")
async def fixture_research_unit_center_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "research_unit_center")


@pytest_asyncio.fixture(name="research_unit_center_pydantic_model")
async def fixture_research_unit_center_pydantic_model(
        research_unit_center_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(research_unit_center_json_data)


@pytest_asyncio.fixture(name="persisted_research_unit_center_pydantic_model")
async def fixture_persisted_research_unit_center_pydantic_model(
        research_unit_center_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(research_unit_center_pydantic_model)
    return research_unit_center_pydantic_model


@pytest_asyncio.fixture(name="research_unit_center_updated_json_data")
async def fixture_research_unit_center_updated_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "research_unit_center_updated")


@pytest_asyncio.fixture(name="research_unit_center_updated_pydantic_model")
async def fixture_research_unit_center_updated_pydantic_model(
        research_unit_center_updated_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(research_unit_center_updated_json_data)


@pytest_asyncio.fixture(name="research_unit_without_labels_json_data")
async def fixture_research_unit_without_labels_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "research_unit_without_labels")
