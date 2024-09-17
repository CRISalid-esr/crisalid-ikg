"""
Settings for test environment
"""
import logging
import sys
from typing import ClassVar

from pydantic_settings import SettingsConfigDict
from pyparsing import TextIO

from app.settings.app_settings import AppSettings


class TestAppSettings(AppSettings):
    """
    Settings for test environment
    """
    __test__ = False

    debug: bool = True

    logging_level: int = logging.DEBUG

    loguru_level: str = "DEBUG"

    logger_sink: ClassVar[str | TextIO] = sys.stderr

    model_config = SettingsConfigDict(env_file=".test.env", extra="ignore")

    amqp_user: str = "rabbitmq_test_user"

    amqp_password: str = "rabbitmq_test_password"

    amqp_host: str = "rabbitmq_test_host"

    institution_name: str = "XYZ University • test"

    neo4j_uri: str = "bolt://localhost:7688"
