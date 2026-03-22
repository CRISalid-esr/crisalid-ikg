"""
App settings base class
"""
import logging
import os
from typing import ClassVar, TextIO, List

import yaml
from pydantic_settings import BaseSettings

from app.models.identifier_types import PersonIdentifierType, OrganizationIdentifierType
from app.settings.app_env_types import AppEnvTypes


class AppSettings(BaseSettings):
    """
    App settings main class with parameters definition
    """

    @staticmethod
    def settings_file_path(filename: str) -> str:
        """
        Get the path of a settings file

        :param filename: The name of the settings file
        :return: The path of the settings file
        """
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "..", "..", filename
        )

    @staticmethod
    def dct_from_yml(yml_file: str) -> dict:
        """
        Load settings from yml file
        """
        with open(yml_file, encoding="utf8") as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    app_env: AppEnvTypes = AppEnvTypes.PROD
    debug: bool = False
    logging_level: int = logging.INFO
    loguru_level: str = "INFO"
    logger_sink: ClassVar[str | TextIO] = "logs/app.log"

    api_prefix: str = "/api"
    api_version: str = "v0"

    amqp_enabled: bool = True

    amqp_user: str = "guest"
    amqp_password: str = "guest"
    amqp_host: str = "127.0.0.1"
    amqp_publications_queue_name: str = "crisalid-ikg-publications"
    amqp_harvesting_events_queue_name: str = "crisalid-ikg-harvesting-events"
    amqp_people_queue_name: str = "crisalid-ikg-people"
    amqp_structures_queue_name: str = "crisalid-ikg-structures"
    amqp_user_actions_queue_name: str = "crisalid-ikg-user-actions"
    amqp_wait_before_shutdown: int = 30
    amqp_task_parallelism_limit: int = 10
    amqp_prefetch_count: int = 10
    amqp_publications_topic: str = "publications"
    amqp_harvesting_events_topic: str = "harvesting_events"
    amqp_publications_exchange_name: str = "publications"
    amqp_people_topic: str = "people"
    amqp_structures_topic: str = "structures"
    amqp_user_actions_topic: str = "user_actions"
    amqp_directory_exchange_name: str = "directory"
    amqp_graph_exchange_name: str = "graph"
    amqp_consumer_ack_timeout: int = 43200000
    amqp_harvester_reference_event_routing_key: str = "event.references.reference.*"
    amqp_harvesting_event_routing_key: str = "event.references.*.*"
    amqp_directory_people_event_routing_key: str = "event.people.person.*"
    amqp_graph_people_event_created_routing_key: str = "event.people.person.created"
    amqp_graph_people_event_updated_routing_key: str = "event.people.person.updated"
    amqp_graph_people_event_deleted_routing_key: str = "event.people.person.deleted"
    amqp_graph_people_event_unchanged_routing_key: str = "event.people.person.unchanged"
    amqp_graph_harvesting_state_event_routing_key: str = "event.harvestings.state.*"
    amqp_graph_harvesting_result_event_routing_key: str = "event.harvestings.result.*"
    amqp_graph_document_task_routing_key: str = "task.documents.document.*"
    amqp_graph_person_documents_fetch_task_routing_key: str = "task.people.documents.fetch"
    amqp_graph_person_attribute_update_task_routing_key: str = "task.people.person.*"
    amqp_graph_research_unit_event_created_routing_key: str = \
        "event.structures.structure.created"
    amqp_graph_research_unit_event_updated_routing_key: str = \
        "event.structures.structure.updated"
    amqp_graph_research_unit_event_deleted_routing_key: str = \
        "event.structures.structure.deleted"
    amqp_graph_research_unit_event_unchanged_routing_key: str = \
        "event.structures.structure.unchanged"
    amqp_graph_document_event_created_routing_key: str = "event.documents.document.created"
    amqp_graph_document_event_updated_routing_key: str = "event.documents.document.updated"
    amqp_graph_document_event_deleted_routing_key: str = "event.documents.document.deleted"
    amqp_graph_document_event_unchanged_routing_key: str = "event.documents.document.unchanged"
    amqp_directory_structure_event_routing_key: str = "event.structures.structure.*"
    amqp_harvester_publication_retrieval_routing_key: str = "task.entity.references.retrieval"

    event_types_to_process: List[str] = [
        "created",
        "updated",
        "unchanged",
        "deleted"
    ]
    # --HARVESTER PLATFORM IDENTIFIERS--
    harvesters: List[str] = ["idref", "scanr", "hal", "openalex", "scopus"]

    org_registry_url: str = "http://localhost:3000"

    institution_name: str = "XYZ University"

    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"

    http_client_limit: int = 100
    http_client_ttl_dns_cache: int = 300
    http_client_timeout_total: float = 7.0

    graph_db: str = "neo4j"

    neo4j_edition: str = "community"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    es_enabled: bool = True
    es_host: str = "http://localhost"
    es_port: int = 9200
    es_user: str = "elastic"
    es_password: str = "elastic"
    es_indexes: dict[str, dict] = {
        "source_records": {
            "index_name": "source_records_index"
        }
    }

    person_identifier_order: list[PersonIdentifierType] = \
        [PersonIdentifierType.LOCAL,
         PersonIdentifierType.ORCID,
         PersonIdentifierType.IDREF]

    research_unit_identifier_order: list[OrganizationIdentifierType] = \
        [OrganizationIdentifierType.LOCAL,
         OrganizationIdentifierType.IDREF,
         OrganizationIdentifierType.ROR]

    institution_identifier_order: list[OrganizationIdentifierType] = \
        [OrganizationIdentifierType.UAI,
         OrganizationIdentifierType.ROR,
         OrganizationIdentifierType.IDREF]

    publication_source_policies_file: str = settings_file_path(
        filename="publication_sources_policies.yaml")
    publication_source_policies: dict = dct_from_yml(yml_file=publication_source_policies_file)

    coauthor_names_maximal_distance: int = 30
    reluctance_to_fuzzy_match_authors: int = 3  # 1 is low, 10 is high, 30 is very high

    issn_check_delay: int = 3 * 30 * 24 * 60 * 60  # 3 months in seconds

    email_unpaywall:str = 'test@test.com'
