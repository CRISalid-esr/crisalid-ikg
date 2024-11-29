from enum import Enum
from typing import Tuple, NamedTuple, List

from neo4j import AsyncManagedTransaction

from app.errors.conflict_error import ConflictError
from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.concepts import Concept
from app.models.journal_identifiers import JournalIdentifier
from app.models.literal import Literal
from app.models.people import Person
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_issue import SourceIssue
from app.models.source_journal import SourceJournal
from app.models.source_records import SourceRecord


class SourceRecordDAO(Neo4jDAO):
    """
    Data access object for source records and the neo4j database
    """

    class UpdateStatus(NamedTuple):
        """
        Update status details
        """
        identifiers_changed: bool
        titles_changed: bool
        contributors_changed: bool

    class EquivalenceType(Enum):
        """
        Enum for equivalence between source records types
        """
        ALL = ":INFERRED_EQUIVALENT|:ASSERTED_EQUIVALENT|:PREDICTED_EQUIVALENT"
        INFERRED = ":INFERRED_EQUIVALENT"
        ASSERTED = ":ASSERTED_EQUIVALENT"
        PREDICTED = ":PREDICTED_EQUIVALENT"

    @handle_database_errors
    async def create(self, source_record: SourceRecord,
                     harvested_for: Person
                     ) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create  a source record in the graph database

        :param harvested_for: person on behalf of whom the source record was harvested
        :param source_record: source record object
        :return: source record uid, operation status and update status details
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_source_record_transaction,
                                                source_record,
                                                harvested_for
                                                )
        return source_record.uid, SourceRecordDAO.Status.CREATED, None

    @handle_database_errors
    async def update(self, source_record: SourceRecord,
                     harvested_for: Person
                     ) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Update a source record in the graph database

        :param harvested_for: person on behalf of whom the source record was harvested
        :param source_record: source record object
        :return: source record uid, operation status and update status details
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._update_source_record_transaction(tx, source_record,
                                                                        harvested_for)

    @handle_database_errors
    async def get_source_records_with_shared_identifier_uids(self, source_record_id: str):
        """
        Get source records with shared publication identifiers
        :param source_record_id:
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_source_records_with_shared_identifier_uids(
                        tx,
                        source_record_id)

    @handle_database_errors
    async def get_source_records_equivalent_uids(self, source_record_uid: str,
                                                 equivalence_type: EquivalenceType) -> List[str]:
        """
        Get the equivalent UIDs of a source record based on the specified equivalence type.
        :param source_record_uid: The UID of the source record.
        :param equivalence_type: The type of equivalence (INFERRED, ASSERTED, PREDICTED).
        :return: A list of equivalent UIDs.
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_source_records_equivalent_uids(tx, source_record_uid,
                                                                          equivalence_type)

    @handle_database_errors
    async def delete_inferred_equivalence_relationships(self, source_record_uid: str,
                                                        target_source_record_uids: list[str]):
        """
        Delete inferred equivalent relationships between a source record and other source records
        :param source_record_uid:
        :param target_source_record_uids:
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._delete_inferred_equivalence_relationships(
                        tx,
                        source_record_uid,
                        target_source_record_uids)

    @handle_database_errors
    async def create_inferred_equivalence_relationships(self, source_record_uids: list[str]):
        """
        Create inferred equivalent relationships between a source record and other source records
        :param source_record_uids:
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._create_inferred_equivalence_relationships(tx,
                                                                                 source_record_uids)

    @handle_database_errors
    async def get(self, source_record_uid: str) -> SourceRecord:
        """
        Get a source record from the graph database

        :param source_record_uid: source record uid
        :return: source record object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourceRecordDAO._get_source_record_by_uid(tx, source_record_uid)

    @staticmethod
    async def _source_record_exists(tx: AsyncManagedTransaction, source_record_uid: str) -> bool:
        result = await tx.run(
            load_query("source_record_exists"),
            source_record_uid=source_record_uid
        )
        record = await result.single()
        return record is not None

    @classmethod
    async def _get_source_record_by_uid(cls, tx: AsyncManagedTransaction,
                                        source_record_uid: str) -> SourceRecord | None:
        result = await tx.run(
            load_query("get_source_record_by_uid"),
            source_record_uid=source_record_uid
        )
        record = await result.single()
        if record:
            return cls._hydrate(record)
        return None

    @classmethod
    async def _create_source_record_transaction(cls, tx: AsyncManagedTransaction,
                                                source_record: SourceRecord,
                                                harvested_for: Person
                                                ):
        if not source_record.uid:
            raise ValueError(f"Unable to compute primary key for source record {source_record}")
        if harvested_for is None:
            raise ValueError(
                f"Source record {source_record} must be related to a person"
                "on behalf of whom it was harvested")
        source_record_exists = await SourceRecordDAO._source_record_exists(tx, source_record.uid)
        if source_record_exists:
            raise ConflictError(f"Source record with uid {source_record.uid} already exists")
        create_source_record_query = load_query("create_source_record")
        issue = source_record.issue.model_dump() if source_record.issue else None
        if issue:
            issue.pop("journal", None)
        await tx.run(
            create_source_record_query,
            source_record_uid=source_record.uid,
            source_identifier=source_record.source_identifier,
            harvester=source_record.harvester,
            person_uid=harvested_for.uid,
            issue=issue,
            journal_uid=source_record.issue.journal.uid if source_record.issue and
                                                           source_record.issue.journal else None,
            titles=[title.model_dump() for title in source_record.titles],
            abstracts=[abstract.model_dump() for abstract in source_record.abstracts],
            identifiers=[identifier.dict() for identifier in source_record.identifiers],
            subject_uids=[subject.uid for subject in source_record.subjects]
        )

    @classmethod
    async def _update_source_record_transaction(cls, tx: AsyncManagedTransaction,
                                                source_record: SourceRecord,
                                                harvested_for: Person
                                                ) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        if not source_record.uid:
            raise ValueError(f"Unable to compute primary key for source record {source_record}")
        if harvested_for is None:
            raise ValueError(
                f"Source record {source_record} must be related to a person"
                "on behalf of whom it was harvested")
        source_record_exists = await SourceRecordDAO._source_record_exists(tx, source_record.uid)
        if not source_record_exists:
            raise ValueError(f"Source record with uid {source_record.uid} does not exist")
        update_source_record_query = load_query("update_source_record")
        issue = source_record.issue.model_dump() if source_record.issue else None
        if issue:
            issue.pop("journal", None)
        await tx.run(
            update_source_record_query,
            source_record_uid=source_record.uid,
            source_identifier=source_record.source_identifier,
            harvester=source_record.harvester,
            person_uid=harvested_for.uid,
            issue=issue,
            journal_uid=source_record.issue.journal.uid if source_record.issue and
                                                           source_record.issue.journal else None,
            titles=[title.model_dump() for title in source_record.titles],
            abstracts=[abstract.model_dump() for abstract in source_record.abstracts],
            identifiers=[identifier.dict() for identifier in source_record.identifiers],
            subject_uids=[subject.uid for subject in source_record.subjects]
        )
        return source_record.uid, SourceRecordDAO.Status.UPDATED, None

    @classmethod
    async def _get_source_records_with_shared_identifier_uids(cls, tx: AsyncManagedTransaction,
                                                              source_record_uid: str):
        result = await tx.run(
            load_query("get_source_records_with_shared_identifier_uids"),
            source_record_uid=source_record_uid
        )
        record = await result.single()
        return record["uids"] if record else []

    @classmethod
    async def _get_source_records_equivalent_uids(cls, tx: AsyncManagedTransaction,
                                                  source_record_uid: str,
                                                  equivalence_type: EquivalenceType) -> List[str]:
        """
        Internal method to fetch equivalent UIDs based on equivalence type.
        :param tx: The database transaction.
        :param source_record_uid: The UID of the source record.
        :param equivalence_type: The type of equivalence (INFERRED, ASSERTED, PREDICTED).
        :return: A list of equivalent UIDs.
        """
        query = load_query("get_source_records_equivalent_uids")
        result = await tx.run(
            query,
            source_record_uid=source_record_uid,
            relationship_filter=f"{equivalence_type.value}"
        )
        record = await result.single()
        return record["uids"] if record else []

    @classmethod
    async def _delete_inferred_equivalence_relationships(cls, tx: AsyncManagedTransaction,
                                                         source_record_uid: str,
                                                         target_source_record_uids: list[str]):
        await tx.run(
            load_query("delete_inferred_equivalence_relationships"),
            source_record_uid=source_record_uid,
            target_source_record_uids=target_source_record_uids
        )

    @classmethod
    async def _create_inferred_equivalence_relationships(cls, tx: AsyncManagedTransaction,
                                                         source_record_uids: list[str]):
        await tx.run(
            load_query("create_inferred_equivalence_relationships"),
            source_record_uids=source_record_uids
        )

    @staticmethod
    def _hydrate(record) -> SourceRecord:
        source_record = SourceRecord(
            uid=record["s"]["uid"],
            source_identifier=record["s"]["source_identifier"],
            harvester=record["s"]["harvester"],
            titles=[Literal(**title) for title in record["titles"]],
            harvested_for_uids=record['harvested_for_uids'],
        )
        for abstract in record["abstracts"]:
            source_record.abstracts.append(Literal(**abstract))
        for identifier in record["identifiers"]:
            source_record.identifiers.append(PublicationIdentifier(**identifier))
        for subject in record["subjects"]:
            source_record.subjects.append(Concept(
                uid=subject['uid'],
                uri=subject['uri']))
        if record["journal"]:
            journal = SourceJournal(**record["journal"])
            if record["journal_identifiers"]:
                for identifier in record["journal_identifiers"]:
                    journal.identifiers.append(  # pylint: disable=no-member
                        JournalIdentifier(**identifier))
            if record["issue"]:
                issue = dict(record["issue"]) | {"journal": journal}
                source_record.issue = SourceIssue(**issue)
        return source_record
