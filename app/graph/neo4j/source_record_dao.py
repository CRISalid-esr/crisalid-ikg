from typing import Tuple, NamedTuple

from neo4j import AsyncManagedTransaction

from app.errors.conflict_error import ConflictError
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.literal import Literal
from app.models.people import Person
from app.models.publication_identifiers import PublicationIdentifier
from app.models.source_records import SourceRecord
from app.services.identifiers.identifier_service import AgentIdentifierService


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

    async def create(self, source_record: SourceRecord,
                     harvested_for: Person
                     ) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create  a source record in the graph database

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
            load_query("get_source_record_by_id"),
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
        source_record.uid = source_record.uid or cls._compute_source_record_uid(
            source_record)
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
        await tx.run(
            create_source_record_query,
            source_record_uid=source_record.uid,
            source_identifier=source_record.source_identifier,
            harvester=source_record.harvester,
            person_uid=harvested_for.uid,
            titles=[title.dict() for title in source_record.titles],
            abstracts=[abstract.dict() for abstract in source_record.abstracts],
            identifiers=[identifier.dict() for identifier in source_record.identifiers]
        )

    @staticmethod
    def _hydrate(record) -> SourceRecord:
        source_record = SourceRecord(
            uid=record["s"]["uid"],
            source_identifier=record["s"]["source_identifier"],
            harvester=record["s"]["harvester"],
            titles=[],
            identifiers=[]
        )
        for title in record["titles"]:
            source_record.titles.append(Literal(**title))
        for abstract in record["abstracts"]:
            source_record.abstracts.append(Literal(**abstract))
        for identifier in record["identifiers"]:
            source_record.identifiers.append(PublicationIdentifier(**identifier))
        return source_record

    @staticmethod
    def _compute_source_record_uid(source_record: SourceRecord) -> str:
        if not source_record.source_identifier or not source_record.harvester:
            raise ValueError(
                f"Source record {source_record} must have a source identifier and a harvester")
        return f"{source_record.harvester}" \
               f"{AgentIdentifierService.IDENTIFIER_SEPARATOR}" \
               f"{source_record.source_identifier}"
