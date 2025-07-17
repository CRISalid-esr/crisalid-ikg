from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.document import Document
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentSubjectsChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the subjects of a Document.
    """

    async def apply(self) -> None:
        subject_uids = self.change.parameters.get("conceptUids")

        if not isinstance(subject_uids, list) or not all(
                isinstance(uid, str) for uid in subject_uids):
            raise ValueError(f"Invalid 'conceptUids' in parameters: {self.change.parameters}")
        document_uid = self.change.target_uid
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")
        await self._get_document_dao().remove_subjects(document_uid=document_uid,
                                                       subject_uids=subject_uids)

    def _get_document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        return cast(DocumentDAO, factory.get_dao(Document))

    def _get_dao_factory(self):
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
