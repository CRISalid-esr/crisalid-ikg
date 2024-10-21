from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.source_journal_dao import SourceJournalDAO
from app.models.journal_identifiers import JournalIdentifier
from app.models.source_journal import SourceJournal


async def test_create_source_journal(open_alex_source_journal_pydantic_model: SourceJournal):
    """
    Given a source journal Pydantic model
    When the create method is called
    Then the concept should be created in the database

    :param person_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao: SourceJournalDAO = factory.get_dao(SourceJournal)
    await dao.create(open_alex_source_journal_pydantic_model)
    source_journal_from_db = await dao.get_by_uid(open_alex_source_journal_pydantic_model.uid)
    assert source_journal_from_db
    assert source_journal_from_db.source == open_alex_source_journal_pydantic_model.source
    assert source_journal_from_db.source_identifier == \
           open_alex_source_journal_pydantic_model.source_identifier
    assert "Sample Journal Title" in source_journal_from_db.titles
    assert source_journal_from_db.publisher == "Example Publisher"
    for identifier in open_alex_source_journal_pydantic_model.identifiers:
        assert any(identifier.value == identifier_from_db.value
                   and identifier.type == identifier_from_db.type
                   for identifier_from_db in source_journal_from_db.identifiers)


async def test_update_source_journal(open_alex_source_journal_pydantic_model: SourceJournal):
    """
    Given a source journal Pydantic model
    When the update method is called
    Then the concept should be updated in the database

    :param person_a_pydantic_model:
    :return:
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao: SourceJournalDAO = factory.get_dao(SourceJournal)
    await dao.create(open_alex_source_journal_pydantic_model)
    source_journal_from_db = await dao.get_by_uid(open_alex_source_journal_pydantic_model.uid)
    source_journal_from_db.publisher = "New publisher"
    source_journal_from_db.titles.append("New title")
    source_journal_from_db.identifiers = [
        identifier for identifier in source_journal_from_db.identifiers
        if identifier.value != "0007-4217"
    ]
    source_journal_from_db.identifiers.append(JournalIdentifier(value="8765-4321", type="issn"))
    await dao.update(source_journal_from_db)
    source_journal_from_db = await dao.get_by_uid(open_alex_source_journal_pydantic_model.uid)
    assert source_journal_from_db.publisher == "New publisher"
    assert "New title" in source_journal_from_db.titles
    assert "Sample Journal Title" in source_journal_from_db.titles
    assert "0007-4217" not in [identifier.value for identifier in
                               source_journal_from_db.identifiers]
    assert "8765-4321" in [identifier.value for identifier in source_journal_from_db.identifiers]
