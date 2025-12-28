import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_organization_dao import SourceOrganizationDAO
from app.models.source_organizations import SourceOrganization


@pytest_asyncio.fixture(name="hal_source_institution_pydantic_model")
async def fixture_hal_source_institution_pydantic_model(
        hal_source_institution_json_data) -> SourceOrganization:
    """
    Create a source journal pydantic model
    :param hal_source_institution_json_data:
    :return: basic source record pydantic model from ScanR data
    """
    return SourceOrganization(**hal_source_institution_json_data)


@pytest_asyncio.fixture(name="hal_source_laboratory_pydantic_model")
async def fixture_hal_source_laboratory_pydantic_model(
        hal_source_laboratory_json_data) -> SourceOrganization:
    """
    Create a source journal pydantic model
    :param hal_source_laboratory_json_data:
    :return: basic source record pydantic model from ScanR data
    """
    return SourceOrganization(**hal_source_laboratory_json_data)


@pytest_asyncio.fixture(name="hal_source_org_without_type_pydantic_model")
async def fixture_hal_source_org_without_type_pydantic_model(
        hal_source_org_without_type_json_data) -> SourceOrganization:
    """
    Create a source organization pydantic model without type
    :param hal_source_org_without_type_json_data:
    :return:
    """
    return SourceOrganization(**hal_source_org_without_type_json_data)


@pytest_asyncio.fixture(name="hal_source_institution_json_data")
async def fixture_hal_source_institution_json_data() -> dict[str, str]:
    """
    Create a source journal pydantic model
    :return: basic source record pydantic model from ScanR data
    """
    return {
        "source": "hal",
        "source_identifier": "2001",
        "name": "Université Anonyme",
        "type": "institution",
        "identifiers": [
            {
                "type": "hal",
                "value": "2001"
            },
            {
                "type": "idref",
                "value": "123456789"
            },
            {
                "type": "isni",
                "value": "000000012345678X"
            },
            {
                "type": "ror",
                "value": "https://ror.org/000000000"
            }
        ]
    }


@pytest_asyncio.fixture(name="hal_source_laboratory_json_data")
async def fixture_hal_source_laboratory_json_data() -> dict[str, str]:
    """
    Create a source journal pydantic model
    :return: basic source record pydantic model from ScanR data
    """
    return {
        "source": "hal",
        "source_identifier": "3002",
        "name": "Laboratoire Interdisciplinaire",
        "type": "laboratory",
        "identifiers": [
            {
                "type": "hal",
                "value": "3002"
            },
            {
                "type": "ror",
                "value": "https://ror.org/000000001"
            }
        ]
    }


@pytest_asyncio.fixture(name="hal_source_org_without_type_json_data")
async def fixture_hal_source_org_without_type_json_data() -> dict[str, str]:
    """
    Create source organization json data without type
    :return:
    """
    return {
        "source": "hal",
        "source_identifier": "9999",
        "name": "Organization Without Type",
        "identifiers": [
            {"type": "hal", "value": "9999"}
        ]
    }


@pytest_asyncio.fixture(name="openalex_peer_source_org_json_data")
async def fixture_openalex_peer_source_org_json_data() -> dict:
    """
    A source organization that should be in the same cluster as hal_source_institution_json_data
    because it shares idref=123456789.
    """
    return {
        "source": "openalex",
        "source_identifier": "oa-inst-1",
        "name": "Université Anonyme (OpenAlex)",
        "type": "institution",
        "identifiers": [
            {"type": "openalex", "value": "https://openalex.org/I111111111"},
            {"type": "idref", "value": "123456789"},  # shared with seed
        ],
    }


@pytest_asyncio.fixture(name="scopus_peer_source_org_json_data")
async def fixture_scopus_peer_source_org_json_data() -> dict:
    """
    Another org in the same cluster, connected transitively via shared ROR with the seed.
    """
    return {
        "source": "scopus",
        "source_identifier": "scp-inst-1",
        "name": "Université Anonyme (Scopus)",
        "type": "institution",
        "identifiers": [
            {"type": "scopus", "value": "60099999"},
            {"type": "ror", "value": "https://ror.org/000000000"},  # shared with seed
        ],
    }


@pytest_asyncio.fixture(name="outside_cluster_source_org_json_data")
async def fixture_outside_cluster_source_org_json_data() -> dict:
    """
    An org that must NOT appear in the seed cluster.
    """
    return {
        "source": "hal",
        "source_identifier": "9998",
        "name": "Completely Other Organization",
        "type": "institution",
        "identifiers": [
            {"type": "hal", "value": "9998"},
            {"type": "idref", "value": "DIFFERENT_IDREF"},
            {"type": "ror", "value": "https://ror.org/999999999"},
        ],
    }


@pytest_asyncio.fixture(name="openalex_peer_source_org_pydantic_model")
async def fixture_openalex_peer_source_org_pydantic_model(
        openalex_peer_source_org_json_data,
) -> SourceOrganization:
    """Create a source organization pydantic model for an openalex peer org"""
    return SourceOrganization(**openalex_peer_source_org_json_data)


@pytest_asyncio.fixture(name="scopus_peer_source_org_pydantic_model")
async def fixture_scopus_peer_source_org_pydantic_model(
        scopus_peer_source_org_json_data,
) -> SourceOrganization:
    """Create a source organization pydantic model for a scopus peer org"""
    return SourceOrganization(**scopus_peer_source_org_json_data)


@pytest_asyncio.fixture(name="outside_cluster_source_org_pydantic_model")
async def fixture_outside_cluster_source_org_pydantic_model(
        outside_cluster_source_org_json_data,
) -> SourceOrganization:
    """Create a source organization pydantic model for an outside cluster org"""
    return SourceOrganization(**outside_cluster_source_org_json_data)


@pytest_asyncio.fixture(name="persisted_cluster_seed_source_org")
async def fixture_persisted_cluster_seed_source_org(
        hal_source_institution_pydantic_model: SourceOrganization,
) -> SourceOrganization:
    """Persist the hal source institution"""
    dao = _get_source_organization_dao()
    await dao.create(hal_source_institution_pydantic_model)
    return hal_source_institution_pydantic_model


@pytest_asyncio.fixture(name="persisted_cluster_peer_source_org_1")
async def fixture_persisted_cluster_peer_source_org_1(
        openalex_peer_source_org_pydantic_model: SourceOrganization,
) -> SourceOrganization:
    """Persist the openalex peer source organization"""
    dao = _get_source_organization_dao()
    await dao.create(openalex_peer_source_org_pydantic_model)
    return openalex_peer_source_org_pydantic_model


@pytest_asyncio.fixture(name="persisted_cluster_peer_source_org_2")
async def fixture_persisted_cluster_peer_source_org_2(
        scopus_peer_source_org_pydantic_model: SourceOrganization,
) -> SourceOrganization:
    """Persist the scopus peer source organization"""
    dao = _get_source_organization_dao()
    await dao.create(scopus_peer_source_org_pydantic_model)
    return scopus_peer_source_org_pydantic_model


@pytest_asyncio.fixture(name="persisted_outside_cluster_source_org")
async def fixture_persisted_outside_cluster_source_org(
        outside_cluster_source_org_pydantic_model: SourceOrganization,
) -> SourceOrganization:
    """Persist the outside cluster source organization"""
    dao = _get_source_organization_dao()
    await dao.create(outside_cluster_source_org_pydantic_model)
    return outside_cluster_source_org_pydantic_model


@pytest_asyncio.fixture(name="hal_conflict_a_json_data")
async def fixture_hal_conflict_a_json_data() -> dict:
    """
    Same idref/isni/ror as conflict_b and scanr_conflict_peer, but different hal value.
    This will create incompatibility on type='hal'.
    """
    return {
        "source": "hal",
        "source_identifier": "111023",
        "name": "École Centrale de Nantes",
        "type": "institution",
        "identifiers": [
            {"type": "hal", "value": "111023"},
            {"type": "idref", "value": "03063525X"},
            {"type": "isni", "value": "0000000122039289"},
            {"type": "ror", "value": "03nh7d505"},
        ],
    }


@pytest_asyncio.fixture(name="hal_conflict_b_json_data")
async def fixture_hal_conflict_b_json_data() -> dict:
    """
    Same idref/isni/ror as conflict_a, but different hal value => conflict for type 'hal'.
    """
    return {
        "source": "hal",
        "source_identifier": "1086798",
        "name": "NANTES UNIVERSITÉ - École Centrale de Nantes",
        "type": "institution",
        "identifiers": [
            {"type": "hal", "value": "1086798"},
            {"type": "idref", "value": "03063525X"},
            {"type": "isni", "value": "0000000122039289"},
            {"type": "ror", "value": "03nh7d505"},
        ],
    }


@pytest_asyncio.fixture(name="scanr_conflict_peer_json_data")
async def fixture_scanr_conflict_peer_json_data() -> dict:
    """
    Connected to the conflict cluster via idref/isni/ror, without hal identifier.
    This is your 'so3' case: it cannot decide which hal state it belongs to => root_only.
    """
    return {
        "source": "scanr",
        "source_identifier": "scanr_idref_03063525X",
        "name": "Centrale Nantes",
        "type": "organization",
        "identifiers": [
            {"type": "idref", "value": "03063525X"},
            {"type": "isni", "value": "0000000122039289"},
            {"type": "ror", "value": "03nh7d505"},
            {"type": "viaf", "value": "168478956"},
        ],
    }


@pytest_asyncio.fixture(name="ambiguous_identifiers_source_org_json_data")
async def fixture_ambiguous_identifiers_source_org_json_data() -> dict:
    """
    Single source org having TWO idref values
    => _prepare_source_orgs must drop type 'idref' for this org.
    """
    return {
        "source": "openalex",
        "source_identifier": "oa-amb-1",
        "name": "Org With Ambiguous IdRef",
        "type": "institution",
        "identifiers": [
            {"type": "openalex", "value": "https://openalex.org/I999999999"},
            {"type": "idref", "value": "IDREF_A"},
            {"type": "idref", "value": "IDREF_B"},  # ambiguous => drop idref in algorithm
            {"type": "ror", "value": "https://ror.org/ambiguous"},
        ],
    }


@pytest_asyncio.fixture(name="hal_conflict_a_pydantic_model")
async def fixture_hal_conflict_a_pydantic_model(hal_conflict_a_json_data) -> SourceOrganization:
    """Create a hal conflict a source organization pydantic model"""
    return SourceOrganization(**hal_conflict_a_json_data)


@pytest_asyncio.fixture(name="hal_conflict_b_pydantic_model")
async def fixture_hal_conflict_b_pydantic_model(hal_conflict_b_json_data) -> SourceOrganization:
    """Create a hal conflict b source organization pydantic model"""
    return SourceOrganization(**hal_conflict_b_json_data)


@pytest_asyncio.fixture(name="scanr_conflict_peer_pydantic_model")
async def fixture_scanr_conflict_peer_pydantic_model(
        scanr_conflict_peer_json_data) -> SourceOrganization:
    """Create a scanr conflict peer source organization pydantic model"""
    return SourceOrganization(**scanr_conflict_peer_json_data)


@pytest_asyncio.fixture(name="ambiguous_identifiers_source_org_pydantic_model")
async def fixture_ambiguous_identifiers_source_org_pydantic_model(
        ambiguous_identifiers_source_org_json_data,
) -> SourceOrganization:
    """Create a source organization pydantic model with ambiguous identifiers"""
    return SourceOrganization(**ambiguous_identifiers_source_org_json_data)


@pytest_asyncio.fixture(name="persisted_conflict_seed_source_org")
async def fixture_persisted_conflict_seed_source_org(
        hal_conflict_a_pydantic_model: SourceOrganization) -> SourceOrganization:
    """
    Persist the hal conflict a source organization
    :param hal_conflict_a_pydantic_model:
    :return:
    """
    dao = _get_source_organization_dao()
    await dao.create(hal_conflict_a_pydantic_model)
    return hal_conflict_a_pydantic_model


@pytest_asyncio.fixture(name="persisted_conflict_peer_source_org_1")
async def fixture_persisted_conflict_peer_source_org_1(
        hal_conflict_b_pydantic_model: SourceOrganization) -> SourceOrganization:
    """
    Persist the hal conflict b source organization
    :param hal_conflict_b_pydantic_model:
    :return:
    """
    dao = _get_source_organization_dao()
    await dao.create(hal_conflict_b_pydantic_model)
    return hal_conflict_b_pydantic_model


@pytest_asyncio.fixture(name="persisted_conflict_peer_source_org_2")
async def fixture_persisted_conflict_peer_source_org_2(
        scanr_conflict_peer_pydantic_model: SourceOrganization) -> SourceOrganization:
    """
    Persist the scanr conflict peer source organization
    :param scanr_conflict_peer_pydantic_model:
    :return:
    """
    dao = _get_source_organization_dao()
    await dao.create(scanr_conflict_peer_pydantic_model)
    return scanr_conflict_peer_pydantic_model


def _get_source_organization_dao() -> SourceOrganizationDAO:
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    return factory.get_dao(SourceOrganization)

@pytest_asyncio.fixture(name="hal_ambiguous_a_json_data")
async def fixture_hal_ambiguous_a_json_data() -> dict:
    """
    A has idref + TWO idhal values => ambiguous on 'idhal'
    """
    return {
        "source": "hal",
        "source_identifier": "amb-idhal-a",
        "name": "Ambiguous IDHAL Org",
        "type": "institution",
        "identifiers": [
            {"type": "idref", "value": "IDREF_SHARED"},
            {"type": "hal", "value": "IDHAL_1"},
            {"type": "hal", "value": "IDHAL_2"},
            {"type": "ror", "value": "https://ror.org/amb-idhal"},
        ],
    }


@pytest_asyncio.fixture(name="hal_single_b_json_data")
async def fixture_hal_single_b_json_data() -> dict:
    """
    B is otherwise compatible with A, but has idhal=1 only
    """
    return {
        "source": "openalex",
        "source_identifier": "amb-idhal-b",
        "name": "Ambiguous IDHAL Org (B)",
        "type": "institution",
        "identifiers": [
            {"type": "idref", "value": "IDREF_SHARED"},
            {"type": "hal", "value": "IDHAL_1"},
            {"type": "ror", "value": "https://ror.org/amb-idhal"},
        ],
    }


@pytest_asyncio.fixture(name="hal_single_c_json_data")
async def fixture_hal_single_c_json_data() -> dict:
    """
    C is otherwise compatible with A, but has idhal=2 only
    """
    return {
        "source": "scopus",
        "source_identifier": "amb-idhal-c",
        "name": "Ambiguous IDHAL Org (C)",
        "type": "institution",
        "identifiers": [
            {"type": "idref", "value": "IDREF_SHARED"},
            {"type": "hal", "value": "IDHAL_2"},
            {"type": "ror", "value": "https://ror.org/amb-idhal"},
        ],
    }


@pytest_asyncio.fixture(name="hal_ambiguous_a_pydantic_model")
async def fixture_hal_ambiguous_a_pydantic_model(hal_ambiguous_a_json_data) -> SourceOrganization:
    """
    Persist the hal ambiguous a source organization
    :param hal_ambiguous_a_json_data:
    :return:
    """
    return SourceOrganization(**hal_ambiguous_a_json_data)


@pytest_asyncio.fixture(name="hal_single_b_pydantic_model")
async def fixture_hal_single_b_pydantic_model(hal_single_b_json_data) -> SourceOrganization:
    """
    Persist the hal single b source organization
    :param hal_single_b_json_data:
    :return:
    """
    return SourceOrganization(**hal_single_b_json_data)


@pytest_asyncio.fixture(name="hal_single_c_pydantic_model")
async def fixture_hal_single_c_pydantic_model(hal_single_c_json_data) -> SourceOrganization:
    """
    Persist the hal single c source organization
    :param hal_single_c_json_data:
    :return:
    """
    return SourceOrganization(**hal_single_c_json_data)
