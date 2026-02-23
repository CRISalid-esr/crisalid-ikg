from neo4j import AsyncManagedTransaction

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.journal import Journal
from app.models.journal_identifiers import JournalIdentifier


class JournalDAO(Neo4jDAO):
    """
    Data access object for journals and the neo4j database
    """

    @handle_database_errors
    async def create(self, journal: Journal
                     ) -> Journal:
        """
        Create  a journal in the graph database

        :param journal: journal Pydantic object
        :return: journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                await session.write_transaction(self._create_journal_transaction,
                                                journal
                                                )
        return journal

    @handle_database_errors
    async def update(self, journal: Journal) -> Journal:
        """
        Update a journal in the graph database

        :param journal: journal Pydantic object
        :return: journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    journal_exists = await JournalDAO._journal_exists(
                        tx,
                        journal.uid)
                    if not journal_exists:
                        raise ValueError(f"Journal with uid {journal.uid} not found")
                    await self._update_journal_transaction(tx,
                                                           journal)
                    return journal

    @handle_database_errors
    async def get_by_uid(self, journal_uid: str) -> Journal:
        """
        Get a journal from the graph database

        :param journal_uid: journal uid
        :return: journal object
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await JournalDAO._get_journal_by_uid(tx, journal_uid)

    @handle_database_errors
    async def get_by_identifier(self, identifier: JournalIdentifier) -> Journal | None:
        """
        Get a journal by its identifier from the graph database

        :param identifier: JournalIdentifier object
        :return: Journal object or None if not found
        """
        async with Neo4jConnexion().get_driver() as driver:
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_journal_by_identifier(tx, identifier)

    @staticmethod
    async def _journal_exists(tx: AsyncManagedTransaction, journal_uid: str) -> bool:
        result = await tx.run(
            load_query("journal_exists"),
            journal_uid=journal_uid
        )
        journal = await result.single()
        return journal is not None

    @classmethod
    async def _get_journal_by_uid(cls, tx: AsyncManagedTransaction,
                                  journal_uid: str) -> Journal | None:
        result = await tx.run(
            load_query("get_journal_by_uid"),
            uid=journal_uid
        )
        journal = await result.single()
        if journal:
            return cls._hydrate(journal)
        return None

    @classmethod
    async def _get_journal_by_identifier(cls, tx: AsyncManagedTransaction,
                                         identifier: JournalIdentifier
                                         ) -> Journal | None:
        result = await tx.run(
            load_query("get_journal_by_identifier"),
            identifier_type=identifier.type.value,
            identifier_value=identifier.value
        )
        journal = await result.single()
        if journal:
            return cls._hydrate(journal)
        return None

    @classmethod
    async def _create_journal_transaction(cls, tx: AsyncManagedTransaction,
                                          journal: Journal
                                          ):
        journal_exists = await JournalDAO._journal_exists(tx,
                                                          journal.uid)
        if journal_exists:
            raise ConflictError(f"Journal with uid {journal.uid} already exists")
        create_journal_query = load_query("create_journal")
        await tx.run(
            create_journal_query,
            journal_uid=journal.uid,
            issn_l=journal.issn_l,
            publisher=journal.publisher,
            titles=journal.titles,
            identifiers=[identifier.dict() for identifier in journal.identifiers],
        )

    async def _update_journal_transaction(self, tx: AsyncManagedTransaction,
                                          journal: Journal
                                          ) -> None:
        journal_exists = await JournalDAO._journal_exists(tx,
                                                          journal.uid)
        if not journal_exists:
            raise ValueError(f"Journal with uid {journal.uid} not found")
        update_journal_query = load_query("update_journal")
        await tx.run(
            update_journal_query,
            journal_uid=journal.uid,
            issn_l=journal.issn_l,
            publisher=journal.publisher,
            titles=journal.titles,
            identifiers=[identifier.dict() for identifier in journal.identifiers],
        )

    @staticmethod
    def _hydrate(record) -> Journal:
        journal = Journal(
            uid=record["j"]["uid"],
            issn_l=record["j"]["issn_l"],
            publisher=record["j"]["publisher"],
            titles=record["j"]["titles"],
            identifiers=[],
        )
        for identifier in record["identifiers"]:
            journal.identifiers = journal.identifiers + [
                JournalIdentifier(**identifier)]
        return journal
