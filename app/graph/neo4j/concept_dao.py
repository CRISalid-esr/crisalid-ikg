from neo4j import AsyncManagedTransaction
from neo4j.exceptions import ConstraintError, ClientError, Neo4jError, DatabaseError

from app.errors.conflict_error import ConflictError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.concepts import Concept
from app.models.literal import Literal
from app.models.people import Person


class ConceptDAO(Neo4jDAO):
    """
    Data access object for concepts and the neo4j database
    """

    async def get(self, concept_id: str) -> Concept | None:
        """
        Get a concept from the graph database

        :param concept_id: concept id
        :return: concept object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await ConceptDAO._get_concept_by_id(tx, concept_id)

    async def find_by_uri(self, uri: str) -> Concept | None:
        """
        Find a concept by its uri

        :param uri: concept uri
        :return: concept object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_concept_by_uri"),
                        uri=uri
                    )
                    record = await result.single()
                    if record:
                        return self._hydrate(record)
                    return None

    @classmethod
    async def _get_concept_by_id(cls, tx, concept_id: str) -> Person | None:
        result = await tx.run(
            load_query("get_concept_by_id"),
            concept_id=concept_id
        )
        record = await result.single()
        if record:
            return cls._hydrate(record)
        return None

    @staticmethod
    def _hydrate(record: dict) -> Person:
        concept_data = record["concept"]
        pref_labels_data = record["pref_labels"]
        alt_labels_data = record["alt_labels"]
        pref_labels = [Literal(**pref_label_data) for pref_label_data in pref_labels_data]
        alt_labels = [Literal(**alt_label_data) for alt_label_data in alt_labels_data]
        concept = Concept(
            uri=concept_data["uri"],
            pref_labels=pref_labels,
            alt_labels=alt_labels
        )
        return concept

    async def create(self, concept: Concept) -> str:
        """
        Create  a concept in the graph database

        :param concept: concept object
        :return: concept id
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_concept_transaction, concept)
        return concept.uri

    @staticmethod
    async def _create_concept_transaction(tx: AsyncManagedTransaction, concept: Concept) -> None:
        concept_exists = await ConceptDAO._concept_exists_by_uri(tx, concept.uri) if concept.uri \
            else await ConceptDAO._concept_exists_by_preflabel(tx, concept.pref_labels[0])
        if concept_exists:
            raise ConflictError(f"Concept identified by {concept.uri or concept.pref_labels[0]} "
                                "already exists")
        create_concept_query = load_query("create_concept")
        try:
            await tx.run(
                create_concept_query,
                uri=concept.uri,
                pref_labels=[pref_label.dict() for pref_label in concept.pref_labels],
                alt_labels=[alt_label.dict() for alt_label in concept.alt_labels]
            )
        except ConstraintError as constraint_error:
            raise ConflictError(
                f"Schema constraint violation while creating concept {concept}") \
                from constraint_error
        except ClientError as client_error:
            raise ValueError(
                f"Bad request error while creating concept {concept}") from client_error
        except Neo4jError as neo4j_error:
            raise DatabaseError(f"Database error while creating concept {concept}") \
                from neo4j_error

    @staticmethod
    async def _concept_exists_by_uri(tx: AsyncManagedTransaction, uri: str) -> bool:
        result = await tx.run(
            load_query("find_concept_by_uri"),
            uri=uri
        )
        return bool(await result.single())

    @staticmethod
    async def _concept_exists_by_preflabel(tx: AsyncManagedTransaction,
                                           pref_label: Literal) -> bool:
        result = await tx.run(
            load_query("find_concept_without_uri_by_label"),
            label=pref_label.value,
        )
        return bool(await result.single())
