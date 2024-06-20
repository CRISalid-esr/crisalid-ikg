from typing import Type

from neo4j import AsyncDriver
from pydantic import BaseModel

from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.neo4j_setup import Neo4jSetup
from app.models.people import Person


class Neo4jDAOFactory(DAOFactory):

    def __init__(self):
        self.driver: AsyncDriver = Neo4jConnexion().get_driver()

    def get_dao(self, object_type: Type[BaseModel]=None) -> Neo4jDAO:
        if object_type is None:
            from app.graph.neo4j.global_dao import GlobalDAO
            return GlobalDAO(driver=self.driver)
        if object_type.__name__ == Person.__name__:
            from app.graph.neo4j.people_dao import PeopleDAO
            return PeopleDAO(driver=self.driver)


    def get_setup(self) -> Neo4jSetup:
        return Neo4jSetup(driver=self.driver)