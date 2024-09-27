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

    @staticmethod
    async def _source_record_exists(tx: AsyncManagedTransaction, source_record_id: str) -> bool:
        result = await tx.run(
            load_query("source_record_exists"),
            source_record_id=source_record_id
        )
        record = await result.single()
        return record is not None

    async def create(self, source_record: SourceRecord,
                     harvested_for: Person
                     ) -> Tuple[
        str, Neo4jDAO.Status, UpdateStatus | None]:
        """
        Create  a source record in the graph database

        :param source_record: source record object
        :return: source record id, operation status and update status details
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(self._create_source_record_transaction,
                                                source_record,
                                                harvested_for
                                                )
        return source_record.id, SourceRecordDAO.Status.CREATED, None

    async def get(self, source_record_id: str) -> SourceRecord:
        """
        Get a source record from the graph database

        :param source_record_id: source record id
        :return: source record object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await SourceRecordDAO._get_source_record_by_id(tx, source_record_id)

    @classmethod
    async def _get_source_record_by_id(cls, tx: AsyncManagedTransaction,
                                       source_record_id: str) -> SourceRecord | None:
        result = await tx.run(
            load_query("get_source_record_by_id"),
            source_record_id=source_record_id
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
        source_record.id = source_record.id or cls._compute_source_record_id(
            source_record)
        if not source_record.id:
            raise ValueError(f"Unable to compute primary key for source record {source_record}")
        if harvested_for is None:
            raise ValueError(
                f"Source record {source_record} must be related to a person"
                "on behalf of whom it was harvested")
        source_record_exists = await SourceRecordDAO._source_record_exists(tx, source_record.id)
        if source_record_exists:
            raise ConflictError(f"Source record with id {source_record.id} already exists")
        create_source_record_query = load_query("create_source_record")
        await tx.run(
            create_source_record_query,
            source_record_id=source_record.id,
            source_identifier=source_record.source_identifier,
            harvester=source_record.harvester,
            person_id=harvested_for.id,
            titles=[title.dict() for title in source_record.titles],
            identifiers=[identifier.dict() for identifier in source_record.identifiers]
        )

    @staticmethod
    def _hydrate(record) -> SourceRecord:
        source_record = SourceRecord(
            id=record["s"]["id"],
            source_identifier=record["s"]["source_identifier"],
            harvester=record["s"]["harvester"],
            titles=[],
            identifiers=[]
        )
        for title in record["titles"]:
            source_record.titles.append(Literal(**title))
        for identifier in record["identifiers"]:
            source_record.identifiers.append(PublicationIdentifier(**identifier))
        return source_record

    @staticmethod
    def _compute_source_record_id(source_record: SourceRecord) -> str:
        if not source_record.source_identifier or not source_record.harvester:
            raise ValueError(
                f"Source record {source_record} must have a source identifier and a harvester")
        return f"{source_record.harvester}" \
               f"{AgentIdentifierService.IDENTIFIER_SEPARATOR}" \
               f"{source_record.source_identifier}"