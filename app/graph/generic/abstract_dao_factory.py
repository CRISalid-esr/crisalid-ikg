from abc import ABC
from enum import Enum

from app.graph.generic.dao_factory import DAOFactory


class AbstractDAOFactory(ABC):
    """
    Abstract Factory for data access objects
    """

    class DaoType(Enum):
        """
        Enumeration of DB backend implementations
        """
        NEO4J = 'neo4j'

    def get_dao_factory(self, dao_type: str) -> DAOFactory:
        """
        Get the DAO factory for the given backend

        :param dao_type: the backend type
        :return:
        """
        if dao_type == self.DaoType.NEO4J.value:
            from app.graph.neo4j.neo4j_dao_factory import Neo4jDAOFactory # pylint: disable=import-outside-toplevel
            return Neo4jDAOFactory()
        raise ValueError(f"Unknown DAO type {dao_type}")
