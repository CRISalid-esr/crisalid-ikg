import pytest

from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.concept_dao import ConceptDAO
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.models.concepts import Concept


async def test_valid_import_creates_hierarchy(persisted_openalex_valid_hierarchy):
    """
    Given valid OpenAlex fixture data (1 domain, 1 field, 1 subfield, 1 topic)
    When import_from_path() is called
    Then all four concept nodes exist in Neo4j with correct labels, pref_labels,
    alt_labels, and a complete BROADER chain
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao: ConceptDAO = factory.get_dao(Concept)

    domain = await dao.find_by_uri("https://openalex.org/domains/3")
    assert domain is not None
    assert any(lb.value == "Physical Sciences" for lb in domain.pref_labels)
    assert any(lb.value == "exact sciences" for lb in domain.alt_labels)

    field = await dao.find_by_uri("https://openalex.org/fields/17")
    assert field is not None
    assert any(lb.value == "Computer Science" for lb in field.pref_labels)
    assert any(lb.value == "informatics" for lb in field.alt_labels)

    subfield = await dao.find_by_uri("https://openalex.org/subfields/1705")
    assert subfield is not None
    assert any(
        lb.value == "Computer Networks and Communications"
        for lb in subfield.pref_labels
    )

    topic = await dao.find_by_uri("https://openalex.org/T11347")
    assert topic is not None
    assert any(
        lb.value == "Neural Networks Stability and Synchronization"
        for lb in topic.pref_labels
    )

    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    "MATCH (t:Topic {uri: $uri})-[:BROADER]->(sf:SubField)"
                    "-[:BROADER]->(f:Field)-[:BROADER]->(d:Domain)"
                    " RETURN t.display_name AS t_name, sf.display_name AS sf_name,"
                    " f.display_name AS f_name, d.display_name AS d_name",
                    uri="https://openalex.org/T11347",
                )
                record = await result.single()
                assert record is not None
                assert record["d_name"] == "Physical Sciences"
                assert record["f_name"] == "Computer Science"
                assert record["sf_name"] == "Computer Networks and Communications"
                assert record["t_name"] == "Neural Networks Stability and Synchronization"


async def test_invalid_import_raises_on_missing_parent(openalex_invalid_tree_path):
    """
    Given an invalid OpenAlex dataset where the topic's parent subfield is absent
    When import_from_path() is called
    Then a ValueError is raised
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    setup = factory.get_domain_setup()
    with pytest.raises(ValueError):
        await setup.import_from_path(openalex_invalid_tree_path)


async def test_update_imports_new_nodes_and_updates_broader(
    persisted_openalex_valid_updated_hierarchy,
):
    """
    Given the valid hierarchy (domain/3, field/17, subfield/1705, topics T11347+T10080)
    is imported first, then a variant (adds field/25 and subfield/2600,
    re-parents T11347 to subfield/2600, omits T10080)
    Then:
    - New nodes (fields/25, subfields/2600) exist in graph
    - T11347 BROADER now points to subfields/2600 (re-parented)
    - T10080 still exists (import is additive, never deletes nodes)
    - T10080 BROADER still points to subfields/1705 (unchanged by variant import)
    """
    factory = AbstractDAOFactory().get_dao_factory("neo4j")
    dao: ConceptDAO = factory.get_dao(Concept)

    math = await dao.find_by_uri("https://openalex.org/fields/25")
    assert math is not None
    assert any(lb.value == "Mathematics" for lb in math.pref_labels)

    applied_math = await dao.find_by_uri("https://openalex.org/subfields/2600")
    assert applied_math is not None
    assert any(lb.value == "Applied Mathematics" for lb in applied_math.pref_labels)

    async with Neo4jConnexion().get_driver() as driver:
        async with driver.session() as session:
            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    "MATCH (t:Topic {uri: $uri})-[:BROADER]->(sf) RETURN sf.uri AS sf_uri",
                    uri="https://openalex.org/T11347",
                )
                record = await result.single()
                assert record is not None
                assert record["sf_uri"] == "https://openalex.org/subfields/2600"

            async with await session.begin_transaction() as tx:
                result = await tx.run(
                    "MATCH (t:Topic {uri: $uri})-[:BROADER]->(sf) RETURN sf.uri AS sf_uri",
                    uri="https://openalex.org/T10080",
                )
                record = await result.single()
                assert record is not None
                assert record["sf_uri"] == "https://openalex.org/subfields/1705"