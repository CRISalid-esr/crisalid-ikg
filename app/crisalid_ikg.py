import asyncio
import sys

from aiormq import AMQPConnectionError
from fastapi import FastAPI
from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_interface import AMQPInterface
from app.config import get_app_settings
from app.errors.validation_error import http422_error_handler
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.routes.api import router as api_router
from app.routes.healthness import router as healthness_router


class CrisalidIKG(FastAPI):
    """Main application, routing logic, middlewares and startup/shutdown events"""

    def __init__(self):
        super().__init__()
        self.amqp_interface = None
        settings = get_app_settings()

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

        self.add_exception_handler(ValidationError, http422_error_handler)

        self.add_event_handler("startup", self.setup_graph)

        if settings.amqp_enabled:
            self.add_event_handler("startup", self.open_rabbitmq_connexion)
            self.add_event_handler("shutdown", self.close_rabbitmq_connexion)

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
    async def open_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Init AMQP connexion at boot time"""
        try:
            logger.info("Enabling RabbitMQ connexion")
            settings = get_app_settings()
            self.amqp_interface = AMQPInterface(settings)
            await self.amqp_interface.connect()
            asyncio.create_task(self.amqp_interface.listen(settings.amqp_people_topic),
                                name="amqp_people_listener")
            asyncio.create_task(self.amqp_interface.listen(settings.amqp_publications_topic),
                                name="amqp_publications_listener")
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

    async def close_rabbitmq_connexion(self) -> None:  # pragma: no cover
        """Handle last tasks before shutdown"""
        logger.info("Closing RabbitMQ connexion")
        await self.amqp_interface.stop_listening()
        logger.info("RabbitMQ connexion has been closed")
