"""
App settings base class
"""
import logging
from typing import ClassVar, TextIO

from pydantic_settings import BaseSettings

from app.models.identifier_types import PersonIdentifierType, OrganizationIdentifierType
from app.settings.app_env_types import AppEnvTypes


class AppSettings(BaseSettings):
    """
    App settings main class with parameters definition
    """

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
    amqp_people_queue_name: str = "crisalid-ikg-people"
    amqp_structures_queue_name: str = "crisalid-ikg-structures"
    amqp_wait_before_shutdown: int = 30
    amqp_task_parallelism_limit: int = 50
    amqp_publications_topic: str = "publications"
    amqp_publications_exchange_name: str = "publications"
    amqp_people_topic: str = "people"
    amqp_structures_topic: str = "structures"
    amqp_directory_exchange_name: str = "directory"
    amqp_prefetch_count: int = 50
    amqp_consumer_ack_timeout: int = 43200000
    amqp_reference_event_routing_key: str = "event.references.reference.*"
    amqp_people_event_routing_key: str = "event.people.person.*"
    amqp_structure_event_routing_key: str = "event.structures.structure.*"
    amqp_publication_retrieval_routing_key: str = "task.entity.references.retrieval"

    institution_name: str = "XYZ University"

    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"

    graph_db: str = "neo4j"

    neo4j_edition: str = "community"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    people_identifier_order: list[PersonIdentifierType] = \
        [PersonIdentifierType.LOCAL,
         PersonIdentifierType.ORCID,
         PersonIdentifierType.IDREF]

    structure_identifier_order: list[OrganizationIdentifierType] = \
        [OrganizationIdentifierType.LOCAL,
         OrganizationIdentifierType.IDREF,
         OrganizationIdentifierType.ROR]
