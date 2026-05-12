from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.agent_identifiers import PersonIdentifier
from app.models.identifier_types import PersonIdentifierType
from app.models.people import Person

_FULLTEXT_QUERY = (
    "CALL db.index.fulltext.queryNodes('person_fulltext_name', $search_query) "
    "YIELD node RETURN node.display_name AS display_name"
)


async def _create_person(display_name: str, identifier_value: str,
                          display_name_variants: list[str] | None = None) -> None:
    person = Person(
        display_name=display_name,
        display_name_variants=display_name_variants or [],
        identifiers=[PersonIdentifier(type=PersonIdentifierType.LOCAL, value=identifier_value)],
    )
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao = factory.get_dao(Person)
    await dao.create(person)


async def _fulltext_search(query: str) -> list[str]:
    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            result = await session.run(_FULLTEXT_QUERY, search_query=query)
            records = await result.data()
    return [r["display_name"] for r in records]


async def test_find_person_with_missing_letter():
    """
    A fuzzy query missing one letter in the first name still finds the person.
    "Piere" (missing second 'r') matches "Pierre" with edit distance 1.
    """
    await _create_person("Pierre Martin", "pierre.martin@test.edu")
    results = await _fulltext_search("Piere~")
    assert "Pierre Martin" in results


async def test_find_person_with_character_substitution():
    """
    A fuzzy query with a substituted character still finds the person.
    "Martun" (u instead of i) matches "Martin" with edit distance 1.
    """
    await _create_person("Pierre Martin", "pierre.martin@test.edu")
    results = await _fulltext_search("Martun~")
    assert "Pierre Martin" in results


async def test_find_person_with_unordered_name():
    """
    Tokens in reversed order still find the person because the full-text
    index matches individual tokens regardless of position.
    """
    await _create_person("Pierre Martin", "pierre.martin@test.edu")
    results = await _fulltext_search("Martin Pierre")
    assert "Pierre Martin" in results


async def test_find_person_without_accented_characters():
    """
    Searching without accents finds the person via display_name_variants,
    which stores the ASCII-normalized form alongside the accented display_name.
    """
    await _create_person(
        "Françoise Lefebvre",
        "francoise.lefebvre@test.edu",
        display_name_variants=["Francoise Lefebvre"],
    )
    results = await _fulltext_search("Francoise")
    assert "Françoise Lefebvre" in results
