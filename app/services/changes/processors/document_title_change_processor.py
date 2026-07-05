from app.models.change_report import ChangeApplicationReport
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentTitleChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the titles of a Document.
    """

    async def apply(self) -> ChangeApplicationReport:

        document_uid = self.change.target_uid
        title = self.change.parameters.get("value")
        language = self.change.parameters.get("language")
        action = self.change.action_type
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")
        try :
            if action == "ADD":
                await self._get_document_dao().add_title(document_uid=document_uid,
                                                       title=title,
                                                       language=language)
            else:
                await self._get_document_dao().remove_title(document_uid=document_uid,
                                                         title=title,
                                                         language=language)

        except ValueError as exc:
            raise ValueError(f"Invalid new document title: {title}") from exc
        return ChangeApplicationReport()
