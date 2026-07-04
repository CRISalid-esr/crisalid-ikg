from app.models.change_report import ChangeApplicationReport
from app.models.text_literal import TextLiteral
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor


class DocumentAbstractChangeProcessor(AbstractChangeProcessor):
    """
    Processor for changes related to the titles of a Document.
    """

    async def apply(self) -> ChangeApplicationReport:

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
        return ChangeApplicationReport()
