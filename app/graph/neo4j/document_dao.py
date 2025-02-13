from loguru import logger
from pydantic import BaseModel
from neo4j import Record, AsyncTransaction, AsyncResult, AsyncManagedTransaction

from app.errors.database_error import handle_database_errors
from app.graph.neo4j.neo4j_connexion import Neo4jConnexion
from app.graph.neo4j.neo4j_dao import Neo4jDAO
from app.graph.neo4j.utils import load_query
from app.models.book import Book
from app.models.book_chapter import BookChapter
from app.models.conference_article import ConferenceArticle
from app.models.contributions import Contribution
from app.models.document import Document
from app.models.journal_article import JournalArticle
from app.models.literal import Literal
from app.models.monograph import Monograph
from app.models.proceedings import Proceedings
from app.models.scholarly_publication import ScholarlyPublication


class DocumentDAO(Neo4jDAO):
    """
    Data access object for publications in the Neo4j graph database
    """

    DOCUMENT_CLASS_MAP = {
        "Document": Document,
        "ScholarlyPublication": ScholarlyPublication,
        "Article": JournalArticle,
        "Book": Book,
        "Monograph": Monograph,
        "BookChapter": BookChapter,
        "ConferenceArticle": ConferenceArticle,
        "Proceedings": Proceedings
    }

    @handle_database_errors
    async def get_document_by_uid(self, uid: str) -> Document | None:
        """
        Get a document by its UID
        :param uid: UID of the document
        :return: Document object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_document_by_uid(tx, uid)

    @handle_database_errors
    async def get_document_uids(self) -> list[str]:
        """
        Get all document uids
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_document_uids(tx)

    @handle_database_errors
    async def create_or_update_document(self, document: Document) -> (
            Document):
        """
        Create  a document

        :type document: a document object
        :return: document object
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                document = await session.write_transaction(
                    self._create_or_update_document_transaction,
                    document=document
                )
        return document

    @handle_database_errors
    async def attach_source_records_to_document(self, document_uid: str,
                                                source_record_uids: list[str]) -> None:
        """
        Attach source records to a document
        :param document_uid: UID of the document
        :param source_record_uids: list of source record UIDs
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(
                    self._attach_source_records_to_document_transaction,
                    document_uid=document_uid,
                    source_record_uids=source_record_uids
                )

    @classmethod
    async def _create_or_update_document_transaction(
            cls, tx: AsyncManagedTransaction,
            document: Document) -> AsyncResult:
        create_document_query = load_query(
            "create_or_update_document"
        )
        labels = cls._get_labels_from_hierarchy(document)
        publication_date_start = document.publication_date_start.isoformat() \
            if document.publication_date_start else None
        publication_date_end = document.publication_date_end.isoformat() \
            if document.publication_date_end else None
        return await tx.run(
            create_document_query,
            document_uid=document.uid,
            document_type=document.type,
            source_record_uids=document.source_record_uids,
            to_be_recomputed=document.to_be_recomputed,
            to_be_deleted=document.to_be_deleted,
            to_be_merged_into_uid=document.to_be_merged_into_uid,
            titles=[title.model_dump() for title in document.titles],
            abstracts=[abstract.model_dump() for abstract in document.abstracts],
            publication_date=document.publication_date,
            publication_date_start=publication_date_start,
            publication_date_end=publication_date_end,
            document_labels=labels.split(":")
        )

    @classmethod
    async def _attach_source_records_to_document_transaction(
            cls, tx: AsyncManagedTransaction, document_uid: str,
            source_record_uids: list[str]) -> None:
        attach_source_records_to_document_query = load_query(
            "attach_source_records_to_document"
        )
        await tx.run(
            attach_source_records_to_document_query,
            document_uid=document_uid,
            source_record_uids=source_record_uids
        )

    @classmethod
    async def _get_document_by_uid(cls, tx: AsyncTransaction, uid: str) -> Document | None:
        """
        Get a document by its UID
        :param tx: Neo4j transaction object
        :param uid: UID of the document
        :return: Document object
        """
        result = await tx.run(
            load_query("get_document_by_uid"),
            document_uid=uid
        )
        record = await result.single()
        return cls._hydrate(record)

    @classmethod
    async def _get_document_uids(cls, tx: AsyncTransaction) -> list[str]:
        """
        Get all document uids
        :param tx: Neo4j transaction object
        :return:
        """
        result = await tx.run(
            load_query("get_document_uids")
        )
        return [record['uid'] async for record in result]

    @handle_database_errors
    async def get_document_by_source_record_uid(
            self, source_record_uid: str) -> Document | None:
        """
        Get the publications attached to a source record
        :param source_record_uid:
        :return:
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                async with await session.begin_transaction() as tx:
                    return await self._get_document_by_source_record_uid(tx,
                                                                         source_record_uid)

    @classmethod
    async def _get_document_by_source_record_uid(cls, tx: AsyncTransaction,
                                                 source_record_uid: str) -> Document | None:
        result = await tx.run(
            load_query("get_document_by_source_record_uid"),
            source_record_uid=source_record_uid
        )
        record = await result.single()
        return cls._hydrate(record)

    @handle_database_errors
    async def create_contribution(
            self,
            document_uid: str,
            person_uid: str,
            roles: list[str]
    ) -> str | None:
        """
        Create a Contribution node and establish relationships to the Document and Person.

        :param document_uid: UID of the Document.
        :param person_uid: UID of the Person.
        :param roles: List of roles to attach to the contribution.
        :return: UID of the created Contribution.
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                return await session.write_transaction(
                    self._create_contribution_transaction,
                    document_uid,
                    person_uid,
                    roles
                )

    @staticmethod
    async def _create_contribution_transaction(
            tx: AsyncManagedTransaction,
            document_uid: str,
            person_uid: str,
            roles: list[str]
    ) -> str | None:
        """
        Transaction to create Contribution and link it to Document and Person.

        :param tx: Neo4j transaction object.
        :param document_uid: UID of the Document.
        :param person_uid: UID of the Person.
        :param roles: List of roles to attach to the contribution.
        :return: id of the created Contribution.
        """
        query = load_query("create_contribution_to_document")
        result = await tx.run(
            query,
            document_uid=document_uid,
            person_uid=person_uid,
            roles=roles
        )
        single = await result.single()
        if single is None:
            return None
        return single['contribution_id']

    @handle_database_errors
    async def delete_contributions_not_in(
            self,
            document_uid: str,
            contribution_ids: list[str]
    ) -> None:
        """
        Delete contributions linked to a Document
        that are not in the specified list of contribution IDs.

        :param document_uid: UID of the Document.
        :param contribution_ids: List of contribution IDs to retain.
        :return: None
        """
        async for driver in Neo4jConnexion().get_driver():
            async with driver.session() as session:
                await session.write_transaction(
                    self._delete_contributions_not_in_transaction,
                    document_uid,
                    contribution_ids
                )

    @staticmethod
    async def _delete_contributions_not_in_transaction(
            tx: AsyncManagedTransaction,
            document_uid: str,
            contribution_ids: list[str]
    ) -> None:
        """
        Transaction to delete contributions linked to a Document
        that are not in the specified list.

        :param tx: Neo4j transaction object.
        :param document_uid: UID of the Document.
        :param contribution_ids: List of contribution IDs to retain.
        :return: None
        """
        query = load_query("delete_contributions_not_in")
        await tx.run(
            query,
            document_uid=document_uid,
            contribution_ids=contribution_ids
        )

    @staticmethod
    def _get_labels_from_hierarchy(document: Document) -> str:
        """
        Get the labels for a document based on its class hierarchy
        e.g. "Document:Publication:Article"
        :return:
        """
        return ":".join(reversed([
            cls.__name__
            for cls in document.__class__.mro()[:-1]  # Exclude object
            if cls not in (BaseModel,)  # Exclude BaseModel
        ]))

    @classmethod
    def _hydrate(cls, record: Record) -> Document | None:
        """
        Hydrate a document object from a Neo4j record
        :param record: Neo4j record
        :return:
        """
        if record is None:
            return None
        labels = record["labels"]

        # Determine the correct class
        document_class = cls._get_concrete_document_class(labels)
        document = document_class(**record['document'])
        document.source_record_uids = [
            source_record['uid'] for source_record in record['source_records']
        ]
        for title in record['titles']:
            document.titles.append(Literal(**title))
        for contribution in record['contributions']:
            document.contributions.append(Contribution(**contribution))

        document.publication_date = record['document'].get('publication_date')

        return document

    @classmethod
    def _get_concrete_document_class(cls, labels: list[str]) -> type[Document]:
        """
        Determines the most specific document class based on Neo4j labels.
        """

        matched_classes = [class_ for class_ in labels if class_ in cls.DOCUMENT_CLASS_MAP]

        if not matched_classes:
            logger.error(f"Unknown document type from labels: {labels}")
            return Document

        most_specific_class = matched_classes[-1]

        return cls.DOCUMENT_CLASS_MAP[most_specific_class]
