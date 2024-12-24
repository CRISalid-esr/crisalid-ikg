from neo4j import AsyncManagedTransaction

from app.config import get_app_settings
from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.agent_identifiers import PersonIdentifier
from app.models.source_people import SourcePerson


class SourcePersonDAO(Neo4jDAO):
    """
    Data access object for source people and the neo4j database
    """

    @handle_database_errors
    async def create(self, source_person: SourcePerson
                     ) -> SourcePerson:
        """
        Create  a source person in the graph database

        :param source_person: source person Pydantic object
        :return: source person object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_source_person_transaction,
                                                source_person
                                                )
        return source_person

    @handle_database_errors
    async def update(self, source_person: SourcePerson) -> SourcePerson:
        """
        Update a source person in the graph database

        :param source_person: source person Pydantic object
        :return: source person object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    source_person_exists = await SourcePersonDAO._source_person_exists(
                        tx,
                        source_person.uid)
                    if not source_person_exists:
                        raise ValueError(f"Source person with uid {source_person.uid} not found")
                    await self._update_source_person_transaction(tx,
                                                                 source_person)
                    return source_person

    @handle_database_errors
    async def source_person_exists(self, source_person_uid: str) -> bool:
        """
        Check if a source person exists in the graph database

        :param source_person_uid: source person uid
        :return: True if the source person exists, False otherwise
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourcePersonDAO._source_person_exists(tx, source_person_uid)

    @handle_database_errors
    async def create_distances(self, source_people_uids: list[str],
                               distances: dict, textual_document_uid: str) -> None:
        """
        Register distances relationships between source people in the graph database.

        :param source_people_uids: global source people list, even if there is no
                path between them
        :param distances: precomputed distances between source people
        :param textual_document_uid: the context document in which the distances are computed
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._create_distances(tx, source_people_uids, distances,
                                                        textual_document_uid)

    @staticmethod
    @handle_database_errors
    async def _create_distances(tx: AsyncManagedTransaction, source_people_uids: list[str]
                                , distances: dict,
                                textual_document_uid: str) -> None:
        """
        Internal method to create distances in the database.

        :param tx: Transaction object.
        :param source_people_uids: global source people list,
                even if there is no path between them.
        :param distances: precomputed distances between source people.
        :param textual_document_uid: the context document in which the distances are computed.
        """
        query = load_query("create_distances_between_source_people")
        # réticene à rapprocher les auteurs de façon floue
        origin_distance = get_app_settings().reluctance_to_fuzzy_match_authors
        await tx.run(
            query,
            source_people_uids=source_people_uids,
            distances=distances,
            textual_document_uid=textual_document_uid,
            origin_distance=origin_distance
        )


    @handle_database_errors
    async def get_by_uid(self, source_person_uid: str) -> SourcePerson:
        """
        Get a source person from the graph database

        :param source_person_uid: source person uid
        :return: source person object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourcePersonDAO._get_source_person_by_uid(tx, source_person_uid)

    @staticmethod
    async def _source_person_exists(tx: AsyncManagedTransaction, source_person_uid: str) -> bool:
        result = await tx.run(
            load_query("source_person_exists"),
            source_person_uid=source_person_uid
        )
        person = await result.single()
        return person is not None

    @classmethod
    async def _get_source_person_by_uid(cls, tx: AsyncManagedTransaction,
                                        source_person_uid: str) -> SourcePerson | None:
        result = await tx.run(
            load_query("get_source_person_by_uid"),
            uid=source_person_uid
        )
        source_person = await result.single()
        if source_person:
            return cls._hydrate(source_person)
        return None

    @classmethod
    async def _create_source_person_transaction(cls, tx: AsyncManagedTransaction,
                                                source_person: SourcePerson
                                                ):
        source_person_exists = await SourcePersonDAO._source_person_exists(tx,
                                                                           source_person.uid)
        if source_person_exists:
            raise ConflictError(f"Source person with uid {source_person.uid} already exists")
        create_source_person_query = load_query("create_source_person")
        await tx.run(
            create_source_person_query,
            source_person_uid=source_person.uid,
            source=source_person.source,
            source_identifier=source_person.source_identifier,
            name=source_person.name,
            identifiers=[identifier.model_dump() for identifier in source_person.identifiers],
        )

    @classmethod
    async def _update_source_person_transaction(cls, tx: AsyncManagedTransaction,
                                                source_person: SourcePerson
                                                ) -> None:
        source_person_exists = await SourcePersonDAO._source_person_exists(tx,
                                                                           source_person.uid)
        if not source_person_exists:
            raise ValueError(f"Source person with uid {source_person.uid} not found")
        update_source_person_query = load_query("update_source_person")
        await tx.run(
            update_source_person_query,
            source_person_uid=source_person.uid,
            source=source_person.source,
            source_identifier=source_person.source_identifier,
            name=source_person.name,
            identifiers=[identifier.model_dump() for identifier in source_person.identifiers],
        )

    @staticmethod
    def _hydrate(record) -> SourcePerson:
        source_person = SourcePerson(
            uid=record["s"]["uid"],
            source=record["s"]["source"],
            source_identifier=record["s"]["source_identifier"],
            name=record["s"]["name"],
            identifiers=[]
        )
        for identifier in record["identifiers"]:
            source_person.identifiers = source_person.identifiers + [
                PersonIdentifier(**identifier)]
        return source_person
