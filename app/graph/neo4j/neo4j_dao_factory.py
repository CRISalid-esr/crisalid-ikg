from typing import Type

from neo4j import AsyncDriver
from pydantic import BaseModel

from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.neo4j_setup import Neo4jSetup
from app.models.people import Person
from app.models.research_structures import ResearchStructure
from app.models.source_records import SourceRecord


class Neo4jDAOFactory(DAOFactory):
    """
    Factory to get the DAO instances for Neo4j
    """

    def __init__(self):
        self.driver: AsyncDriver = Neo4jConnexion().get_driver()

    def get_dao(self, object_type: Type[BaseModel] = None) -> Neo4jDAO:
        if object_type is None:
            from app.graph.neo4j.global_dao import \
                GlobalDAO  # pylint: disable=import-outside-toplevel
            return GlobalDAO(driver=self.driver)
        if object_type.__name__ == Person.__name__:
            from app.graph.neo4j.people_dao import \
                PeopleDAO  # pylint: disable=import-outside-toplevel
            return PeopleDAO(driver=self.driver)
        if object_type.__name__ == ResearchStructure.__name__:
            from app.graph.neo4j.research_structure_dao import \
                ResearchStructureDAO  # pylint: disable=import-outside-toplevel
            return ResearchStructureDAO(driver=self.driver)
        if object_type.__name__ == SourceRecord.__name__:
            from app.graph.neo4j.source_record_dao import \
                SourceRecordDAO  # pylint: disable=import-outside-toplevel
            return SourceRecordDAO(driver=self.driver)
        raise ValueError(f"Unsupported object type: {object_type}")

    def get_setup(self) -> Neo4jSetup:
        return Neo4jSetup(driver=self.driver)
