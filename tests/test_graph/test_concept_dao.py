from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.models.concepts import Concept


async def test_create_concept(concept_a_pydantic_model: Concept):
    """
    Given a basic concept Pydantic model
    When the create method is called
    Then the concept should be created in the database

    :param person_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Concept)
    await dao.create(concept_a_pydantic_model)
    concept_from_db = await dao.find_by_uri(concept_a_pydantic_model.uri)
    assert concept_from_db
    assert concept_from_db.uri == concept_a_pydantic_model.uri
    for pref_label in concept_a_pydantic_model.pref_labels:
        assert any(pref_label.value == pref_label_from_db.value
                   and pref_label.language == pref_label_from_db.language
                   for pref_label_from_db in concept_from_db.pref_labels)
    for alt_label in concept_a_pydantic_model.alt_labels:
        assert any(alt_label.value == alt_label_from_db.value
                   and alt_label.language == alt_label_from_db.language
                   for alt_label_from_db in concept_from_db.alt_labels)
