from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentTypeChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the type of a Document.
    """

    async def apply(self) -> None:

        document_uid = self.change.target_uid
        new_type = self.change.parameters.get("value")
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")
        await self._get_document_dao().update_type(document_uid=document_uid,
                                                       type=new_type)

    def _get_document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        return cast(DocumentDAO, factory.get_dao(Document))

    def _get_dao_factory(self):
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
