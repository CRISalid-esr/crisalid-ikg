from typing import NamedTuple

from neo4j import AsyncManagedTransaction, AsyncTransaction

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.journal_identifiers import JournalIdentifier
from app.models.source_journal import SourceJournal


class SourceJournalDAO(Neo4jDAO):
    """
    Data access object for source journals and the neo4j database
    """

    class UpdateStatus(NamedTuple):
        """
        Update status details
        """
        identifiers_changed: bool
        titles_changed: bool

    @handle_database_errors
    async def create(self, source_journal: SourceJournal
                     ) -> SourceJournal:
        """
        Create  a source journal in the graph database

        :param source_journal: source journal Pydantic object
        :return: source journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_source_journal_transaction,
                                                source_journal
                                                )
        return source_journal

    @handle_database_errors
    async def update(self, source_journal: SourceJournal) -> SourceJournal:
        """
        Update a source journal in the graph database

        :param source_journal: source journal Pydantic object
        :return: source journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    source_journal_exists = await SourceJournalDAO._source_journal_exists(
                        tx,
                        source_journal.uid)
                    if not source_journal_exists:
                        raise ValueError(f"Source journal with uid {source_journal.uid} not found")
                    await self._update_source_journal_transaction(tx,
                                                                  source_journal)
                    return source_journal

    @handle_database_errors
    async def get_by_uid(self, source_journal_uid: str) -> SourceJournal:
        """
        Get a source journal from the graph database

        :param source_journal_uid: source journal uid
        :return: source journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourceJournalDAO._get_source_journal_by_uid(tx, source_journal_uid)

    @handle_database_errors
    async def get_source_journal_uids(self) -> list[str]:
        """
        Get all source journal UIDs from the graph database
        :return:
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_source_journal_uids(tx)

    @staticmethod
    async def _source_journal_exists(tx: AsyncManagedTransaction, source_journal_uid: str) -> bool:
        result = await tx.run(
            load_query("source_journal_exists"),
            source_journal_uid=source_journal_uid
        )
        journal = await result.single()
        return journal is not None

    @classmethod
    async def _get_source_journal_by_uid(cls, tx: AsyncManagedTransaction,
                                         source_journal_uid: str) -> SourceJournal | None:
        result = await tx.run(
            load_query("get_source_journal_by_uid"),
            uid=source_journal_uid
        )
        source_journal = await result.single()
        if source_journal:
            return cls._hydrate(source_journal)
        return None

    @classmethod
    async def _get_source_journal_uids(cls, tx: AsyncTransaction) -> list[str]:
        """
        Get all source journal UIDs from the graph database
        :param tx: Neo4j transaction object
        :return:
        """
        result = await tx.run(
            load_query("get_source_journal_uids")
        )
        return [record['uid'] async for record in result]

    @classmethod
    async def _create_source_journal_transaction(cls, tx: AsyncManagedTransaction,
                                                 source_journal: SourceJournal
                                                 ):
        source_journal_exists = await SourceJournalDAO._source_journal_exists(tx,
                                                                              source_journal.uid)
        if source_journal_exists:
            raise ConflictError(f"Source journal with uid {source_journal.uid} already exists")
        create_source_journal_query = load_query("create_source_journal")
        await tx.run(
            create_source_journal_query,
            source_journal_uid=source_journal.uid,
            source=source_journal.source,
            source_identifier=source_journal.source_identifier,
            publisher=source_journal.publisher,
            titles=source_journal.titles,
            identifiers=[identifier.dict() for identifier in source_journal.identifiers],
        )

    async def _update_source_journal_transaction(self, tx: AsyncManagedTransaction,
                                                 source_journal: SourceJournal
                                                 ) -> None:
        source_journal_exists = await SourceJournalDAO._source_journal_exists(tx,
                                                                              source_journal.uid)
        if not source_journal_exists:
            raise ValueError(f"Source journal with uid {source_journal.uid} not found")
        update_source_journal_query = load_query("update_source_journal")
        await tx.run(
            update_source_journal_query,
            source_journal_uid=source_journal.uid,
            source=source_journal.source,
            source_identifier=source_journal.source_identifier,
            publisher=source_journal.publisher,
            titles=source_journal.titles,
            identifiers=[identifier.dict() for identifier in source_journal.identifiers],
        )

    @staticmethod
    def _hydrate(record) -> SourceJournal:
        source_journal = SourceJournal(
            uid=record["s"]["uid"],
            source=record["s"]["source"],
            source_identifier=record["s"]["source_identifier"],
            publisher=record["s"]["publisher"],
            titles=record["s"]["titles"],
            identifiers=[]
        )
        for identifier in record["identifiers"]:
            source_journal.identifiers = source_journal.identifiers + [
                JournalIdentifier(**identifier)]
        return source_journal
