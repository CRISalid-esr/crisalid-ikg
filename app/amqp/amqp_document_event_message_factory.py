import asyncio
from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.documents.document_service import DocumentService


class AMQPDocumentEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to research structures events."""

    @staticmethod
    async def _build_document_message_payload(document_uid: str, retries=0) -> dict[
                                                                                   str, Any
                                                                               ] or None:
        if document_uid is None:
            logger.error("Connot build AMQP message payload without document UID")
            return
        document_service = DocumentService()
        try:
            document = await document_service.get_document(document_uid)
        except DatabaseError as e:
            logger.error(f"Error fetching document {document_uid} from database: {e}"
                         "while building AMQP message payload")
            return
        if document is None:
            logger.error(
                f"Document {document_uid} not found in database, new attempt after 1 second")
            if retries < 3:
                await asyncio.sleep(1)
                return await AMQPDocumentEventMessageFactory._build_document_message_payload(
                    document_uid, retries + 1)
            logger.error(f"Document {document_uid} not found in database after 3 attempts")
            return
        return {
            "uid": document.uid,
            "titles": [title.model_dump() for title in document.titles],
            "abstracts": [abstract.model_dump() for abstract in document.abstracts],
            "subjects": [subject.model_dump() for subject in document.subjects],
            "contributions": [contribution.model_dump() for contribution in document.contributions]
        }
