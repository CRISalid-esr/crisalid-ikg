from neo4j import AsyncManagedTransaction

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.concepts import Concept


class OpenAlexConceptDAO(Neo4jDAO):
    """
    Data access object for OpenAlex domain/field/subfield/topic concepts
    """

    _TYPE_QUERIES = {
        "Domain": "upsert_openalex_domain",
        "Field": "upsert_openalex_field",
        "SubField": "upsert_openalex_subfield",
        "Topic": "upsert_openalex_topic",
    }

    @handle_database_errors
    async def upsert(self, concept: Concept, concept_type: str) -> None:
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(
                    self._upsert_transaction, concept, concept_type
                )

    @handle_database_errors
    async def set_broader(self, child_uri: str, parent_uri: str) -> None:
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        "MATCH (c:Concept {uri: $uri}) RETURN c",
                        uri=parent_uri,
                    )
                    if not await result.single():
                        raise ValueError(
                            f"Parent concept {parent_uri} not found in graph "
                            f"(child: {child_uri})"
                        )
                await session.write_transaction(
                    self._set_broader_transaction, child_uri, parent_uri
                )

    @staticmethod
    async def _upsert_transaction(
        tx: AsyncManagedTransaction, concept: Concept, concept_type: str
    ) -> None:
        query_name = OpenAlexConceptDAO._TYPE_QUERIES[concept_type]
        display_name = concept.pref_labels[0].value if concept.pref_labels else ""
        await tx.run(load_query(query_name), uri=concept.uri, display_name=display_name)
        await tx.run(
            load_query("sync_openalex_concept_pref_labels"),
            uri=concept.uri,
            pref_labels=[lb.model_dump() for lb in concept.pref_labels],
        )
        await tx.run(
            load_query("sync_openalex_concept_alt_labels"),
            uri=concept.uri,
            alt_labels=[lb.model_dump() for lb in concept.alt_labels],
        )
        await tx.run(
            load_query("sync_openalex_concept_definition"),
            uri=concept.uri,
            definition=concept.definition.model_dump() if concept.definition else None,
        )

    @staticmethod
    async def _set_broader_transaction(
        tx: AsyncManagedTransaction, child_uri: str, parent_uri: str
    ) -> None:
        await tx.run(
            load_query("set_openalex_broader"),
            child_uri=child_uri,
            parent_uri=parent_uri,
        )
