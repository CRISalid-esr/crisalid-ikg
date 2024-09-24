import json
import pathlib

import pytest

from app.models.people import Person
from app.models.research_structures import ResearchStructure
from app.models.source_records import SourceRecord


@pytest.fixture(name="_base_path")
def fixture_base_path() -> pathlib.Path:
    """Get the current folder of the test"""
    return pathlib.Path(__file__).parent.parent


def _json_data_from_file(base_path, file_path) -> dict:
    file = pathlib.Path(base_path / file_path)
    with open(file, encoding="utf-8") as json_file:
        input_data = json_file.read()
    return json.loads(input_data)


def _person_json_data_from_file(base_path, person) -> dict:
    file_path = f"data/people/{person}.json"
    return _json_data_from_file(base_path, file_path)


def _person_from_json_data(input_data: dict) -> Person:
    return Person(**input_data)


def _organization_json_data_from_file(base_path, structure) -> dict:
    file_path = f"data/organizations/{structure}.json"
    return _json_data_from_file(base_path, file_path)


def _research_structure_from_json_data(input_data: dict) -> ResearchStructure:
    return ResearchStructure(**input_data)


def _source_record_json_data_from_file(base_path, source_record) -> dict:
    file_path = f"data/source_records/{source_record}.json"
    return _json_data_from_file(base_path, file_path)


def _source_record_from_json_data(input_data: dict) -> SourceRecord:
    return SourceRecord(**input_data)
