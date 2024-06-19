from neo4j import AsyncDriver

from app.graph.generic.dao import DAO


class Neo4jDAO(DAO[AsyncDriver]):
    pass
