from typing import AsyncGenerator

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.config import get_app_settings


class Neo4jConnexion:
    async def get_driver(self) -> AsyncGenerator[AsyncDriver, None]:
        settings = get_app_settings()
        driver = AsyncGraphDatabase.driver(settings.neo4j_uri,
                                           auth=(
                                               settings.neo4j_user,
                                               settings.neo4j_password
                                           ))
        try:
            yield driver
        finally:
            await driver.close()
