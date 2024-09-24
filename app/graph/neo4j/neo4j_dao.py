from neo4j import AsyncDriver

from app.graph.generic.dao import DAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.literal import Literal


class Neo4jDAO(DAO[AsyncDriver]):
    """
    Parent class for all Neo4j DAO classes
    """

    IDENTIFIER_SEPARATOR = '-'  # separator for unique identifiers generated from multiple fields

    async def find_literals_by_value_and_language(self, value: str, language: str) -> list[Literal]:
        """
        Find literals by value and language

        :param value: literal value
        :param language: literal language
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        self._find_literals_by_value_and_language_query,
                        value=value,
                        language=language
                    )
                    records = [record.values() async for record in result]
                    literals = [Literal(**dict(record[0])) for record in records]
                    return literals

    _find_literals_by_value_and_language_query = """
        MATCH (l:Literal {value: $value, language: $language})
        RETURN l
    """
