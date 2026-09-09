from app.models.change_report import ChangeApplicationReport
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentTypeChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the type of a Document.
    """

    async def apply(self) -> ChangeApplicationReport:

        document_uid = self.change.target_uid
        new_type = self.change.parameters.get("value")
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")
        try :
            await self._get_document_dao().update_type(document_uid=document_uid,
                                                       new_type=new_type)
        except ValueError as exc:
            raise ValueError(f"Invalid new document type: {new_type}") from exc
        return ChangeApplicationReport()
