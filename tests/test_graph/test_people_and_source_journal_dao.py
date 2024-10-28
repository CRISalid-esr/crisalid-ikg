from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_record_dao import SourceRecordDAO
from app.models.people import Person
from app.models.source_records import SourceRecord

async def test_update_person_concepts(
        persisted_person_a_pydantic_model: Person,
        idref_record_with_person_a_as_contributor_pydantic_model: SourceRecord
):
    """
    Given an existing person Pydantic model,
    When two source record are added for this person with the same concepts,
    Then the records should share the owner and the concepts
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao: SourceRecordDAO = factory.get_dao(SourceRecord)
    await dao.create(idref_record_with_person_a_as_contributor_pydantic_model, persisted_person_a_pydantic_model)
    source_records_from_db = await dao.get(
        idref_record_with_person_a_as_contributor_pydantic_model.uid)
    assert source_records_from_db
