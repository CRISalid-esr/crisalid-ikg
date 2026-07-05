from app.models.change_report import ChangeApplicationReport
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor
from app.services.contributions.contribution_update_service import ContributionUpdateService


class DocumentContributionsChangeProcessor(AbstractChangeProcessor):
    """
    Processor for a full-state contribution update of a Document.

    The change carries the complete desired contributor list in
    ``parameters["contributions"]``; the document's contributions are reconciled to exactly
    that list (replace semantics).
    """

    async def apply(self) -> ChangeApplicationReport:
        document_uid = self.change.target_uid
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")

        contributions = self.change.parameters.get("contributions")
        if not isinstance(contributions, list):
            raise ValueError(
                f"Invalid 'contributions' in parameters of change {self.change.uid}: "
                f"expected a list, got {type(contributions).__name__}")

        return await ContributionUpdateService().reconcile(
            document_uid=document_uid,
            contributions=contributions,
        )
