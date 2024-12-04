from neo4j import Record, AsyncTransaction, AsyncResult, AsyncManagedTransaction

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.document import Document
from app.models.literal import Literal
from app.models.textual_document import TextualDocument


class DocumentDAO(Neo4jDAO):
    """
    Data access object for publications in the Neo4j graph database
    """

    @handle_database_errors
    async def create_or_update_textual_document(self, textual_document: TextualDocument) -> (
            TextualDocument):
        """
        Create  a textual document

        :type textual_document: a textual document object
        :return: textual document object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                textual_document = await session.write_transaction(
                    self._create_or_update_textual_document_transaction,
                    textual_document=textual_document
                )
        return textual_document

    @handle_database_errors
    async def attach_source_records_to_textual_document(self, document_uid: str,
                                                        source_record_uids: list[str]) -> None:
        """
        Attach source records to a textual document
        :param document_uid: UID of the textual document
        :param source_record_uids: list of source record UIDs
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(
                    self._attach_source_records_to_textual_document_transaction,
                    document_uid=document_uid,
                    source_record_uids=source_record_uids
                )

    @classmethod
    async def _create_or_update_textual_document_transaction(
            cls, tx: AsyncManagedTransaction,
            textual_document: TextualDocument) -> AsyncResult:
        create_textual_document_query = load_query(
            "create_or_update_textual_document"
        )
        return await tx.run(
            create_textual_document_query,
            document_uid=textual_document.uid,
            source_record_uids=textual_document.source_record_uids,
            to_be_recomputed=textual_document.to_be_recomputed,
            to_be_deleted=textual_document.to_be_deleted,
            to_be_merged_into_uid=textual_document.to_be_merged_into_uid,
            titles=[title.model_dump() for title in textual_document.titles],
            abstracts=[abstract.model_dump() for abstract in textual_document.abstracts]
        )

    @classmethod
    async def _attach_source_records_to_textual_document_transaction(
            cls, tx: AsyncManagedTransaction, document_uid: str,
            source_record_uids: list[str]) -> None:
        attach_source_records_to_textual_document_query = load_query(
            "attach_source_records_to_textual_document"
        )
        await tx.run(
            attach_source_records_to_textual_document_query,
            document_uid=document_uid,
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
    async def _get_textual_document_by_source_record_uid(cls, tx: AsyncTransaction,
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
        :param record: Neo4j record
        :return:
        """
        if record is None:
            return None
        document = Document(**record['document'])
        document.source_record_uids = record['source_record_uids']
        for title in record['titles']:
            document.titles.append(Literal(**title))
        return document
