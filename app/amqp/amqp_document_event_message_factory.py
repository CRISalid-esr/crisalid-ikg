from typing import Any

from loguru import logger

from app.amqp.abstract_amqp_message_factory import AbstractAMQPMessageFactory
from app.errors.database_error import DatabaseError
from app.services.documents.textual_document_service import TextualDocumentService


class AMQPDocumentEventMessageFactory(AbstractAMQPMessageFactory):
    """Factory for building AMQP messages related to research structures events."""

    @staticmethod
    async def _build_document_message_payload(document_uid: str) -> dict[
                                                                        str, Any] or None:
        if document_uid is None:
            logger.error("Connot build AMQP message payload without document UID")
            return
        textual_document_service = TextualDocumentService()
        try:
            document = await textual_document_service.get_textual_document(document_uid)
        except DatabaseError as e:
            logger.error(f"Error fetching document {document_uid} from database: {e}"
                         "while building AMQP message payload")
            return
        return {
            "uid": document.uid,
            "titles": [title.model_dump() for title in document.titles],
            "abstracts": [abstract.model_dump() for abstract in document.abstracts],
            "subjects": [subject.model_dump() for subject in document.subjects],
            "contributions": [contribution.model_dump() for contribution in document.contributions]
        }
