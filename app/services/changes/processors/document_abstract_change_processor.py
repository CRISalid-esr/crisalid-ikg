from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.models.text_literal import TextLiteral
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentAbstractChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the titles of a Document.
    """

    async def apply(self) -> None:

        document_uid = self.change.target_uid
        abstract_value = self.change.parameters.get("value")
        abstract_language = self.change.parameters.get("language")
        action = self.change.action_type
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")
        try :
            abstract = TextLiteral(value=abstract_value, language=abstract_language)
            if action == "ADD":
                await self._get_document_dao().add_abstract(document_uid=document_uid,
                                                       abstract=abstract)
            else:
                await self._get_document_dao().remove_abstract(document_uid=document_uid,
                                                         abstract=abstract)

        except ValueError as exc:
            raise ValueError(f"Invalid new document abstract: {abstract_value}") from exc

    def _get_document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        return cast(DocumentDAO, factory.get_dao(Document))

    def _get_dao_factory(self):
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
