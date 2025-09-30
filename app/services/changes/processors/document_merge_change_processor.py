from typing import Set, List, Optional

from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor
from app.services.documents.document_service import DocumentService


class DocumentMergeChangeProcessor(AbstractChangeProcessor):
    """
    Processor for user-initiated document merge actions.
    """

    async def apply(self) -> None:

        params = self.change.parameters or {}
        merged_list: Optional[List[str]] = None

        if not isinstance(self.change.target_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")

        if isinstance(params.get("mergedDocumentUids"), list):
            merged_list = params.get("mergedDocumentUids")

        if (
                not isinstance(merged_list, list) or
                not all(isinstance(u, str) and u for u in merged_list)
        ):
            raise ValueError(
                f"Invalid document UID list in parameters: {params}. "
                f"Expected 'mergedDocumentUids' or 'documentUids' as a non-empty list of strings."
            )

        all_uids: Set[str] = set(merged_list)
        all_uids.add(self.change.target_uid)

        if len(all_uids) < 2:
            raise ValueError(
                "Merge requires at least two distinct document UIDs "
                f"(got: {sorted(all_uids)})"
            )

        service = DocumentService()
        await service.merge_documents(all_uids)
