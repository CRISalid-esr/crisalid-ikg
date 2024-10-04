from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.generic.dao import DAO
from app.graph.neo4j.concept_dao import ConceptDAO
from app.models.concepts import Concept
from app.models.literal import Literal


class ConceptService:
    """
    Service to handle operations on people data
    """

    async def create_or_update_concept(self, concept: Concept) -> Concept:
        """
        Create or update a concept in the graph database from a Pydantic Concept object
        :param concept: Pydantic Concept object
        :return:
        """
        factory = self._get_dao_factory()
        dao: ConceptDAO = factory.get_dao(Concept)
        if concept.uri:
            existing_concept = await dao.find_by_uri(concept.uri)
            # case when the concept already exists in the database
            if existing_concept:
                await self._update_concept(existing_concept, concept, dao)
                return existing_concept
            # case when the concept does not exist in the database
            await dao.create(concept)
            return concept
        # case when the concept has no uri
        if len(concept.pref_labels) > 1 or concept.alt_labels:
            raise ValueError(
                "Concept with more than one pref_label or with alt_labels should have an uri")
        existing_concept = await dao.find_concept_without_uri_by_pref_label(concept.pref_labels[0])
        # case when the concept already exists in the database
        if existing_concept:
            return existing_concept
        # case when the concept does not exist in the database
        await dao.create(concept)
        return concept

    async def _update_concept(self, existing_concept: Concept, new_concept: Concept,
                              dao: ConceptDAO) -> None:
        for pref_label in new_concept.pref_labels:
            # if the pref_label already exists in the concept, update it
            if any(
                    existing_pref_label.language == pref_label.language
                    for existing_pref_label in existing_concept.pref_labels
            ):
                existing_concept.pref_labels = [
                    pref_label
                    if pref_label.language == existing_pref_label.language
                    else existing_pref_label
                    for existing_pref_label in existing_concept.pref_labels
                ]
            # if the pref_label does not exist in the concept, add it
            else:
                existing_concept.pref_labels.append(pref_label)
        for alt_label in new_concept.alt_labels:
            # if the alt_label does not exist in the concept, add it
            if not any(
                    existing_alt_label.language == alt_label.language
                    and existing_alt_label.value == alt_label.value
                    for existing_alt_label in existing_concept.alt_labels
            ):
                existing_concept.alt_labels.append(alt_label)
        await dao.update(existing_concept)

    async def get_concept(self, uri: str) -> Concept:
        """
        Get a concept from the graph database by its uri
        :param uri: uri of the concept
        :return: concept
        """
        factory = self._get_dao_factory()
        dao: ConceptDAO = factory.get_dao(Concept)
        return await dao.find_by_uri(uri)

    async def find_concept_without_uri_by_pref_label(self, pref_label: Literal) -> Concept:
        """
        Get a concept from the graph database by its pref_label
        :param pref_label: pref_label of the concept
        :return: concept
        """
        factory = self._get_dao_factory()
        dao: ConceptDAO = factory.get_dao(Concept)
        return await dao.find_concept_without_uri_by_pref_label(pref_label)

    @staticmethod
    def _get_dao_factory() -> DAO:
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
