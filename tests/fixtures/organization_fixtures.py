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


# ── Complex hierarchy fixtures ─────────────────────────────────────────────────

@pytest_asyncio.fixture(name="epe_paris_sud_ouest_json_data")
async def fixture_epe_paris_sud_ouest_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "epe_paris_sud_ouest")


@pytest_asyncio.fixture(name="epe_paris_sud_ouest_pydantic_model")
async def fixture_epe_paris_sud_ouest_pydantic_model(epe_paris_sud_ouest_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(epe_paris_sud_ouest_json_data)


@pytest_asyncio.fixture(name="persisted_epe_paris_sud_ouest_pydantic_model")
async def fixture_persisted_epe_paris_sud_ouest_pydantic_model(
        epe_paris_sud_ouest_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(epe_paris_sud_ouest_pydantic_model)
    return epe_paris_sud_ouest_pydantic_model


@pytest_asyncio.fixture(name="univ_etienne_dupond_json_data")
async def fixture_univ_etienne_dupond_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "univ_etienne_dupond")


@pytest_asyncio.fixture(name="univ_etienne_dupond_pydantic_model")
async def fixture_univ_etienne_dupond_pydantic_model(univ_etienne_dupond_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(univ_etienne_dupond_json_data)


@pytest_asyncio.fixture(name="persisted_univ_etienne_dupond_pydantic_model")
async def fixture_persisted_univ_etienne_dupond_pydantic_model(
        univ_etienne_dupond_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(univ_etienne_dupond_pydantic_model)
    return univ_etienne_dupond_pydantic_model


@pytest_asyncio.fixture(name="cnrs_json_data")
async def fixture_cnrs_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "cnrs")


@pytest_asyncio.fixture(name="cnrs_pydantic_model")
async def fixture_cnrs_pydantic_model(cnrs_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(cnrs_json_data)


@pytest_asyncio.fixture(name="persisted_cnrs_pydantic_model")
async def fixture_persisted_cnrs_pydantic_model(cnrs_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(cnrs_pydantic_model)
    return cnrs_pydantic_model


@pytest_asyncio.fixture(name="ena_astrophysique_json_data")
async def fixture_ena_astrophysique_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "ena_astrophysique")


@pytest_asyncio.fixture(name="ena_astrophysique_pydantic_model")
async def fixture_ena_astrophysique_pydantic_model(ena_astrophysique_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(ena_astrophysique_json_data)


@pytest_asyncio.fixture(name="persisted_ena_astrophysique_pydantic_model")
async def fixture_persisted_ena_astrophysique_pydantic_model(
        ena_astrophysique_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(ena_astrophysique_pydantic_model)
    return ena_astrophysique_pydantic_model


@pytest_asyncio.fixture(name="dept_physique_json_data")
async def fixture_dept_physique_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "dept_physique")


@pytest_asyncio.fixture(name="dept_physique_pydantic_model")
async def fixture_dept_physique_pydantic_model(dept_physique_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(dept_physique_json_data)


@pytest_asyncio.fixture(name="persisted_dept_physique_pydantic_model")
async def fixture_persisted_dept_physique_pydantic_model(
        dept_physique_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(dept_physique_pydantic_model)
    return dept_physique_pydantic_model


@pytest_asyncio.fixture(name="fac_sciences_json_data")
async def fixture_fac_sciences_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "fac_sciences")


@pytest_asyncio.fixture(name="fac_sciences_pydantic_model")
async def fixture_fac_sciences_pydantic_model(fac_sciences_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(fac_sciences_json_data)


@pytest_asyncio.fixture(name="persisted_fac_sciences_pydantic_model")
async def fixture_persisted_fac_sciences_pydantic_model(
        fac_sciences_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(fac_sciences_pydantic_model)
    return fac_sciences_pydantic_model


@pytest_asyncio.fixture(name="lra_research_unit_json_data")
async def fixture_lra_research_unit_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "lra_research_unit")


@pytest_asyncio.fixture(name="lra_research_unit_pydantic_model")
async def fixture_lra_research_unit_pydantic_model(lra_research_unit_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(lra_research_unit_json_data)


@pytest_asyncio.fixture(name="persisted_lra_research_unit_pydantic_model")
async def fixture_persisted_lra_research_unit_pydantic_model(
        lra_research_unit_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(lra_research_unit_pydantic_model)
    return lra_research_unit_pydantic_model


@pytest_asyncio.fixture(name="team_astrophysique_json_data")
async def fixture_team_astrophysique_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "team_astrophysique")


@pytest_asyncio.fixture(name="team_astrophysique_pydantic_model")
async def fixture_team_astrophysique_pydantic_model(team_astrophysique_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(team_astrophysique_json_data)


@pytest_asyncio.fixture(name="persisted_team_astrophysique_pydantic_model")
async def fixture_persisted_team_astrophysique_pydantic_model(
        team_astrophysique_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(team_astrophysique_pydantic_model)
    return team_astrophysique_pydantic_model


@pytest_asyncio.fixture(name="axis_observationnel_json_data")
async def fixture_axis_observationnel_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "axis_observationnel")


@pytest_asyncio.fixture(name="axis_observationnel_pydantic_model")
async def fixture_axis_observationnel_pydantic_model(axis_observationnel_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(axis_observationnel_json_data)


@pytest_asyncio.fixture(name="persisted_axis_observationnel_pydantic_model")
async def fixture_persisted_axis_observationnel_pydantic_model(
        axis_observationnel_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(axis_observationnel_pydantic_model)
    return axis_observationnel_pydantic_model


# ── Evolution step fixtures ────────────────────────────────────────────────────

@pytest_asyncio.fixture(name="ufr_physique_json_data")
async def fixture_ufr_physique_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "ufr_physique")


@pytest_asyncio.fixture(name="ufr_physique_pydantic_model")
async def fixture_ufr_physique_pydantic_model(ufr_physique_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(ufr_physique_json_data)


@pytest_asyncio.fixture(name="persisted_ufr_physique_pydantic_model")
async def fixture_persisted_ufr_physique_pydantic_model(
        ufr_physique_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(ufr_physique_pydantic_model)
    return ufr_physique_pydantic_model


@pytest_asyncio.fixture(name="team_astro_observatoire_json_data")
async def fixture_team_astro_observatoire_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "team_astro_observatoire")


@pytest_asyncio.fixture(name="team_astro_observatoire_pydantic_model")
async def fixture_team_astro_observatoire_pydantic_model(
        team_astro_observatoire_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(team_astro_observatoire_json_data)


@pytest_asyncio.fixture(name="persisted_team_astro_observatoire_pydantic_model")
async def fixture_persisted_team_astro_observatoire_pydantic_model(
        team_astro_observatoire_pydantic_model) -> OrganizationBase:
    settings = get_app_settings()
    factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
    dao = factory.get_dao(OrganizationBase)
    await dao.create(team_astro_observatoire_pydantic_model)
    return team_astro_observatoire_pydantic_model


@pytest_asyncio.fixture(name="lra_research_unit_v2_json_data")
async def fixture_lra_research_unit_v2_json_data(_base_path) -> dict:
    return _organization_unit_json_data_from_file(_base_path, "lra_research_unit_v2")


@pytest_asyncio.fixture(name="lra_research_unit_v2_pydantic_model")
async def fixture_lra_research_unit_v2_pydantic_model(
        lra_research_unit_v2_json_data) -> OrganizationBase:
    return _organization_unit_from_json_data(lra_research_unit_v2_json_data)
