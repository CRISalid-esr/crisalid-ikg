from neo4j import AsyncManagedTransaction, Record

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.document import Document
from app.models.source_records import SourceRecord
from app.models.textual_document import TextualDocument


class DocumentDAO(Neo4jDAO):
    """
    Data access object for publications in the Neo4j graph database
    """

    @handle_database_errors
    async def create_textual_document_from_source_records(self, source_record_uids: list[
        SourceRecord]) -> TextualDocument:
        """
        Create  a textual document from a list of source records

        :param source_record_uids: list of source records recording the textual document
        :return: textual document object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                textual_document = await session.write_transaction(
                    self._create_textual_document_from_source_records_transaction,
                    source_record_uids=source_record_uids
                )
        return textual_document

    @classmethod
    async def _create_textual_document_from_source_records_transaction(
            cls, tx: AsyncManagedTransaction,
            source_record_uids: list[SourceRecord]) -> TextualDocument:
        create_textual_document_from_source_records_query = load_query(
            "create_textual_document_from_source_records"
        )
        await tx.run(
            create_textual_document_from_source_records_query,
            source_record_uids=source_record_uids
        )

    @handle_database_errors
    async def get_textual_document_by_source_record_uid(
            self, source_record_uid: str) -> Document | None:
        """
        Get the publications attached to a source record
        :param source_record_uid:
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_textual_document_by_source_record_uid(tx,
                                                                                 source_record_uid)

    @classmethod
    async def _get_textual_document_by_source_record_uid(cls, tx: AsyncManagedTransaction,
                                                         source_record_uid: str) -> Document | None:
        result = await tx.run(
            load_query("get_textual_document_by_source_record_uid"),
            source_record_uid=source_record_uid
        )
        record = await result.single()
        return cls._hydrate(record)

    @staticmethod
    def _hydrate(record: Record) -> Document | None:
        """
        Hydrate a document object from a Neo4j record
        :param document:
        :return:
        """
        if record is not None:
            return Document(**record['document'])
        return None
