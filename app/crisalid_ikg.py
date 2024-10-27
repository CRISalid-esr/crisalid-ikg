import asyncio
import sys

from aiormq import AMQPConnectionError
from fastapi import FastAPI
from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_interface import AMQPInterface
from app.config import get_app_settings
from app.errors.conflict_error import conflicting_entity_error_handler, ConflictError
from app.errors.not_found_error import not_found_entity_error_handler, NotFoundError
from app.errors.validation_error import invalid_entity_error_handler
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.routes.api import router as api_router
from app.routes.healthness import router as healthness_router
from app.search.search_engine import SearchEngine
from app.search.source_record_index import SourceRecordIndex
from app.signals import person_created, person_identifiers_updated, source_record_created


class CrisalidIKG(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self):
        super().__init__()
        settings = get_app_settings()
        self.amqp_interface = AMQPInterface(settings)
        self.search_engine = None
        self.state.es_client = None

        self.include_router(
            api_router, prefix=f"{settings.api_prefix}/{settings.api_version}"
        )

        self.include_router(healthness_router, prefix="/health")

        logger.remove()
        logger.add(
            settings.logger_sink,
            level=settings.loguru_level,
            **({"rotation": "100 MB"} if settings.logger_sink != sys.stderr else {}),
        )

        self.add_exception_handler(NotFoundError, not_found_entity_error_handler)
        self.add_exception_handler(ConflictError, conflicting_entity_error_handler)
        self.add_exception_handler(ValidationError, invalid_entity_error_handler)

        self.add_event_handler("startup", self.setup_graph)

        if settings.amqp_enabled:
            self.add_event_handler("startup", self.open_rabbitmq_connexion)
            self.add_event_handler("shutdown", self.close_rabbitmq_connexion)

        if settings.es_enabled:
            self.add_event_handler("startup", self.setup_elasticsearch)
            self.add_event_handler("shutdown", self.close_elasticsearch)

        self._register_source_record_events()
        self._register_person_events()

    @logger.catch(reraise=True)
    async def setup_graph(self) -> None:  # pragma: no cover
        """Init graph connexion at boot time"""
        logger.info("Setting up graph connexion")
        settings = get_app_settings()
        factory = AbstractDAOFactory().get_dao_factory(settings.graph_db)
        setup = factory.get_setup()
        await setup.run()
        logger.info("Graph connexion has been set up")

    @logger.catch(reraise=True)
    async def setup_elasticsearch(self) -> None:  # pragma: no cover
        """Init elasticsearch connexion at boot time"""
        logger.info("Setting up elasticsearch connexion")
        self.search_engine = SearchEngine()
        try:
            await self.search_engine.setup_elasticsearch()
            self.state.es_client = self.search_engine.es_client
        except Exception as error:
            logger.error(f"Cannot connect to Elasticsearch : {error}")
            raise error
        logger.info("Elasticsearch connexion has been set up")

    def _register_source_record_events(self):
        self.source_record_index = SourceRecordIndex(app_state=self.state)
        source_record_created.connect(self.source_record_index.add_source_record)

    @logger.catch(reraise=True)
    async def close_elasticsearch(self) -> None:  # pragma: no cover
        """Close elasticsearch connexion at shutdown"""
        logger.info("Closing elasticsearch connexion")
        await self.search_engine.close_elasticsearch()
        logger.info("Elasticsearch connexion has been closed")


    @logger.catch(reraise=True)
    async def open_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Init AMQP connexion at boot time"""
        try:
            logger.info("Enabling RabbitMQ connexion")
            settings = get_app_settings()
            await self.amqp_interface.connect()
            asyncio.create_task(self.amqp_interface.listen(settings.amqp_people_topic),
                                name="amqp_people_listener")
            asyncio.create_task(self.amqp_interface.listen(settings.amqp_publications_topic),
                                name="amqp_publications_listener")
            asyncio.create_task(self.amqp_interface.listen(settings.amqp_structures_topic),
                                name="amqp_structures_listener")
            logger.info("RabbitMQ connexion has been enabled")
        except AMQPConnectionError as error:
            logger.error(
                f"Cannot connect to RabbitMQ : AMQPConnectionError, will retry in 1 second : "
                f"{error}"
            )
            await asyncio.sleep(1)
            await self.open_rabbitmq_connexion()
        except Exception as error:
            logger.error("Cannot connect to RabbitMQ : Unknown error, will not retry")
            raise error


    def _register_person_events(self):
        person_created.connect(self.amqp_interface.fetch_publications)
        person_identifiers_updated.connect(self.amqp_interface.fetch_publications)


    async def close_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Handle last tasks before shutdown"""
        logger.info("Closing RabbitMQ connexion")
        await self.amqp_interface.stop_listening()
        logger.info("RabbitMQ connexion has been closed")
