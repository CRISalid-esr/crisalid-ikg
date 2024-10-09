from neo4j import AsyncSession

from app.config import get_app_settings
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.settings.app_env_types import AppEnvTypes


class GlobalDAO(Neo4jDAO):
    """
    Global DAO to manage global operations on the database
    """

    async def reset_all(self) -> None:
        """
        Reset the database by deleting all nodes and relationships

        :return: None
        """
        settings = get_app_settings()
        # if environment is not test, raise an error
        if settings.app_env not in [AppEnvTypes.TEST, AppEnvTypes.DEV]:
            raise ValueError("This method is only available in the test or dev environment")
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._reset_all_transaction)

    @staticmethod
    async def _reset_all_transaction(tx: AsyncSession) -> None:
        """
        Reset the database by deleting all nodes and relationships

        :param tx: Neo4j transaction
        :return: None
        """
        await tx.run(load_query("reset_all_transactions"))
