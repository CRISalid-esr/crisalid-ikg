import pathlib

import pytest
import pytest_asyncio

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory


@pytest.fixture(name="openalex_valid_tree_path")
def fixture_openalex_valid_tree_path(_base_path) -> str:
    """
    Return the path to the valid OpenAlex test fixture directory.
    :return: path to tests/data/domains/openalex-valid
    """
    return str(pathlib.Path(_base_path) / "data" / "domains" / "openalex-valid")


@pytest.fixture(name="openalex_invalid_tree_path")
def fixture_openalex_invalid_tree_path(_base_path) -> str:
    """
    Return the path to the invalid OpenAlex test fixture directory.
    The topic in this dataset references a subfield that is absent.
    :return: path to tests/data/domains/openalex-invalid
    """
    return str(pathlib.Path(_base_path) / "data" / "domains" / "openalex-invalid")


@pytest_asyncio.fixture(name="persisted_openalex_valid_hierarchy")
async def fixture_persisted_openalex_valid_hierarchy(openalex_valid_tree_path: str) -> None:
    """
    Populate the graph with the valid OpenAlex test hierarchy
    (1 domain, 1 field, 1 subfield, 2 topics) without deleting the source files.
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    setup = factory.get_domain_setup()
    await setup.import_from_path(openalex_valid_tree_path)


@pytest.fixture(name="openalex_valid_variant_tree_path")
def fixture_openalex_valid_variant_tree_path(_base_path) -> str:
    """
    Return the path to the variant OpenAlex test fixture directory.
    Contains the same domain, both original fields plus Mathematics (fields/25),
    both original subfields plus Applied Mathematics (subfields/2600),
    and T11347 re-parented to subfields/2600. T10080 is absent.
    :return: path to tests/data/domains/openalex-valid-variant
    """
    return str(pathlib.Path(_base_path) / "data" / "domains" / "openalex-valid-variant")


@pytest_asyncio.fixture(name="persisted_openalex_valid_updated_hierarchy")
async def fixture_persisted_openalex_valid_updated_hierarchy(
    openalex_valid_tree_path: str,
    openalex_valid_variant_tree_path: str,
) -> None:
    """
    Import the valid hierarchy first, then the variant on top of it.
    Simulates a second import run with updated data.
    """
    factory = AbstractDAOFactory().get_dao_factory(get_app_settings().graph_db)
    setup = factory.get_domain_setup()
    await setup.import_from_path(openalex_valid_tree_path)
    await setup.import_from_path(openalex_valid_variant_tree_path)
