from abc import ABC
from enum import Enum

from app.graph.generic.dao_factory import DAOFactory


class AbstractDAOFactory(ABC):
    class DaoType(Enum):
        NEO4J = 'neo4j'

    def get_dao_factory(self, dao_type: str) -> DAOFactory:
        if dao_type == self.DaoType.NEO4J.value:
            from app.graph.neo4j.neo4j_dao_factory import Neo4jDAOFactory
            return Neo4jDAOFactory()
