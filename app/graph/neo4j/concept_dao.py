from neo4j import AsyncManagedTransaction
from neo4j.exceptions import ConstraintError, ClientError, Neo4jError

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors, DatabaseError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.concepts import Concept
from app.models.literal import Literal


class ConceptDAO(Neo4jDAO):
    """
    Data access object for concepts and the neo4j database
    """

    @handle_database_errors
    async def find_by_uid(self, uid: str) -> Concept | None:
        """
        Find a concept by its uid

        :param uid: concept uid
        :return: concept object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    result = await tx.run(
                        load_query("find_concept_by_uid"),
                        uid=uid
                    )
                    record = await result.single()
                    if record:
                        return self._hydrate(record)

    @handle_database_errors
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

    @handle_database_errors
    async def create(self, concept: Concept) -> str:
        """
        Create  a concept in the graph database

        :param concept: concept object
        :return: concept uid
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_concept_transaction, concept)
        return concept.uri

    @handle_database_errors
    async def update(self, concept: Concept) -> str:
        """
        Update a concept in the graph database

        :param concept: concept object
        :return: concept uid
        """
        existing_concept = await self.find_by_uri(concept.uri)
        if not concept:
            raise ConflictError(
                f"Concept identified by {concept.uri} cannot be updated as it does not exist")
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._update_concept_transaction, concept,
                                                existing_concept)
        return concept.uri

    @staticmethod
    def _hydrate(record: dict) -> Concept:
        concept_data = record["concept"]
        pref_labels_data = record["pref_labels"]
        alt_labels_data = record["alt_labels"]
        pref_labels = [Literal(**pref_label_data) for pref_label_data in pref_labels_data]
        alt_labels = [Literal(**alt_label_data) for alt_label_data in alt_labels_data]
        concept = Concept(
            uid=concept_data["uid"],
            uri=concept_data["uri"],
            pref_labels=pref_labels,
            alt_labels=alt_labels
        )
        return concept

    @staticmethod
    async def _create_concept_transaction(tx: AsyncManagedTransaction, concept: Concept) -> None:
        concept_exists = await ConceptDAO._concept_exists_by_uid(tx, concept.uid)
        if concept_exists:
            raise ConflictError(f"Concept identified by "
                                f"{concept.uri or concept.pref_labels[0]} (uid : {concept.uid}) "
                                "already exists")
        create_concept_query = load_query("create_concept")
        await tx.run(
            create_concept_query,
            uid=concept.uid,
            uri=concept.uri,
            pref_labels=[pref_label.model_dump() for pref_label in concept.pref_labels],
            alt_labels=[alt_label.model_dump() for alt_label in concept.alt_labels]
        )

    @staticmethod
    async def _update_concept_transaction(tx: AsyncManagedTransaction, new_concept: Concept,
                                          existing_concept: Concept
                                          ) -> None:
        preflabels_to_delete = [pref_label for pref_label in existing_concept.pref_labels
                                if pref_label not in new_concept.pref_labels]
        altlabels_to_delete = []

        pref_labels_to_create = [pref_label for pref_label in new_concept.pref_labels

                                 if pref_label not in existing_concept.pref_labels]
        alt_labels_to_create = [alt_label for alt_label in new_concept.alt_labels
                                if alt_label not in existing_concept.alt_labels]
        try:
            if preflabels_to_delete:
                delete_pref_labels_query = load_query("delete_concept_pref_labels")
                await tx.run(
                    delete_pref_labels_query,
                    uri=new_concept.uri,
                    pref_labels=[pref_label.model_dump(exclude_none=True) for pref_label in
                                 preflabels_to_delete]
                )
            if altlabels_to_delete:
                delete_alt_labels_query = load_query("delete_concept_alt_labels")
                await tx.run(
                    delete_alt_labels_query,
                    uid=new_concept.uid,
                    uri=new_concept.uri,
                    alt_labels=[alt_label.model_dump(exclude_none=True) for alt_label in
                                altlabels_to_delete]
                )
            if pref_labels_to_create or alt_labels_to_create:
                create_labels_query = load_query("create_concept_labels")
                await tx.run(
                    create_labels_query,
                    uid=new_concept.uid,
                    pref_labels=[pref_label.model_dump() for pref_label in pref_labels_to_create],
                    alt_labels=[alt_label.model_dump() for alt_label in alt_labels_to_create]
                )
        except ConstraintError as constraint_error:
            raise ConflictError(
                f"Schema constraint violation while updating concept {new_concept}") \
                from constraint_error
        except ClientError as client_error:
            raise ValueError(
                f"Bad request error while updating concept {new_concept}") from client_error
        except Neo4jError as neo4j_error:
            raise DatabaseError(f"Database error while updating concept {new_concept}") \
                from neo4j_error

    @staticmethod
    async def _concept_exists_by_uid(tx: AsyncManagedTransaction, uid: str) -> bool:
        result = await tx.run(
            load_query("find_concept_by_uid"),
            uid=uid
        )
        return bool(await result.single())

    @staticmethod
    async def _concept_exists_by_uri(tx: AsyncManagedTransaction, uri: str) -> bool:
        result = await tx.run(
            load_query("find_concept_by_uri"),
            uri=uri
        )
        return bool(await result.single())
