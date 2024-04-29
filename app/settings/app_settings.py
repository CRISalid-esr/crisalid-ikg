"""
App settings base class
"""
import logging
import os
from typing import ClassVar, TextIO

from pydantic_settings import BaseSettings

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
    amqp_wait_before_shutdown: int = 30
    amqp_task_parallelism_limit: int = 50
    amqp_publications_exchange_name: str = "publications"
    amqp_prefetch_count: int = 50
    amqp_consumer_ack_timeout: int = 43200000
    amqp_reference_event_routing_key: str = "event.references.reference.*"

    institution_name: str = "XYZ University"

    git_commit: str = "-"
    git_branch: str = "-"
    docker_digest: str = "-"
