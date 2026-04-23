import json
import os
import shutil

from loguru import logger
from neo4j import AsyncDriver

from app.config import get_app_settings
from app.graph.generic.setup import Setup
from app.graph.neo4j.openalex_concept_dao import OpenAlexConceptDAO
from app.models.concepts import Concept, Domain, Field, SubField, Topic
from app.models.literal import Literal


class Neo4jDomainSetup(Setup[AsyncDriver]):
    """
    Imports the OpenAlex domains/fields/subfields/topics hierarchy into Neo4j at startup.
    """

    _ENTITY_TYPES = [
        ("domains", "Domain"),
        ("fields", "Field"),
        ("subfields", "SubField"),
        ("topics", "Topic"),
    ]

    _CONCEPT_CLASSES = {
        "Domain": Domain,
        "Field": Field,
        "SubField": SubField,
        "Topic": Topic,
    }

    async def run(self) -> None:
        path = get_app_settings().openalex_topics_tree_path
        if not path or not os.path.exists(path):
            logger.info("No OpenAlex data found at {}, skipping import", path)
            return
        logger.info("Importing OpenAlex concept hierarchy from {}", path)
        await self.import_from_path(path)
        shutil.rmtree(path)
        logger.info("OpenAlex concept hierarchy imported and source files removed")

    async def import_from_path(self, path: str) -> None:
        """Import hierarchy from an explicit path without deleting source files."""
        dao = OpenAlexConceptDAO(driver=self.driver)
        for dir_name, type_label in self._ENTITY_TYPES:
            await self._import_entity_type(path, dir_name, type_label, dao)

    async def _import_entity_type(
        self, base_path: str, dir_name: str, type_label: str, dao: OpenAlexConceptDAO
    ) -> None:
        entity_dir = os.path.join(base_path, dir_name)
        if not os.path.exists(entity_dir):
            logger.warning("OpenAlex {} directory not found, skipping", dir_name)
            return
        date_dirs = sorted(os.listdir(entity_dir))
        for date_dir in date_dirs:
            date_path = os.path.join(entity_dir, date_dir)
            if not os.path.isdir(date_path):
                continue
            for part_file in sorted(os.listdir(date_path)):
                await self._import_file(
                    os.path.join(date_path, part_file), type_label, dao
                )

    async def _import_file(
        self, file_path: str, type_label: str, dao: OpenAlexConceptDAO
    ) -> None:
        logger.debug("Processing OpenAlex file {}", file_path)
        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                concept, parent_uri = self._map_record(record, type_label)
                await dao.upsert(concept, type_label)
                if parent_uri:
                    await dao.set_broader(concept.uri, parent_uri)

    @classmethod
    def _map_record(cls, record: dict, type_label: str) -> tuple[Concept, str | None]:
        uri = record["id"]
        pref_labels = [Literal(value=record["display_name"], language="en")]
        alt_labels = [
            Literal(value=alt, language="en")
            for alt in (record.get("display_name_alternatives") or [])
        ]
        definition = (
            Literal(value=record["description"], language="en")
            if record.get("description") else None
        )
        concept_cls = cls._CONCEPT_CLASSES[type_label]
        concept = concept_cls(
            uri=uri,
            pref_labels=pref_labels,
            alt_labels=alt_labels,
            definition=definition,
        )
        parent_map: dict[str, str | None] = {
            "Domain": None,
            "Field": (record.get("domain") or {}).get("id"),
            "SubField": (record.get("field") or {}).get("id"),
            "Topic": (record.get("subfield") or {}).get("id"),
        }
        return concept, parent_map[type_label]
