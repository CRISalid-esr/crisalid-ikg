from typing import Type

from pydantic import BaseModel
from neo4j import AsyncDriver

from app.graph.generic.dao_factory import DAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.neo4j_setup import Neo4jSetup
from app.models.concepts import Concept
from app.models.document import Document
from app.models.institution import Institution
from app.models.journal import Journal
from app.models.people import Person
from app.models.research_structures import ResearchStructure
from app.models.source_journal import SourceJournal
from app.models.source_organizations import SourceOrganization
from app.models.source_people import SourcePerson
from app.models.source_records import SourceRecord


class Neo4jDAOFactory(DAOFactory):
    """
    Factory to get the DAO instances for Neo4j
    """

    def __init__(self):
        self.driver: AsyncDriver = Neo4jConnexion().get_driver()

        self.dao_mapping = {
            Person: "app.graph.neo4j.person_dao.PersonDAO",
            ResearchStructure: "app.graph.neo4j.research_structure_dao.ResearchStructureDAO",
            Institution: "app.graph.neo4j.institution_dao.InstitutionDAO",
            SourceRecord: "app.graph.neo4j.source_record_dao.SourceRecordDAO",
            Concept: "app.graph.neo4j.concept_dao.ConceptDAO",
            SourceJournal: "app.graph.neo4j.source_journal_dao.SourceJournalDAO",
            SourceOrganization: "app.graph.neo4j.source_organization_dao.SourceOrganizationDAO",
            SourcePerson: "app.graph.neo4j.source_person_dao.SourcePersonDAO",
            Document: "app.graph.neo4j.document_dao.DocumentDAO",
            Journal: "app.graph.neo4j.journal_dao.JournalDAO",
        }

    def get_dao(self, object_type: Type[BaseModel] = None) -> Neo4jDAO:
        if object_type is None:
            from app.graph.neo4j.global_dao import \
                GlobalDAO  # pylint: disable=import-outside-toplevel
            return GlobalDAO(driver=self.driver)

        dao_class_path = self.dao_mapping.get(object_type)
        if dao_class_path is None:
            raise ValueError(f"Unsupported object type: {object_type}")
        module_path, class_name = dao_class_path.rsplit('.', 1)
        dao_module = __import__(module_path, fromlist=[class_name])
        dao_class = getattr(dao_module, class_name)
        return dao_class(driver=self.driver)

    def get_setup(self) -> Neo4jSetup:
        return Neo4jSetup(driver=self.driver)
