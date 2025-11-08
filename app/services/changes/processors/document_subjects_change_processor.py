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

        document_uid = self.change.target_uid
        if not isinstance(document_uid, str):
            raise ValueError(f"Invalid 'targetUid' in change: {self.change.target_uid}")

        if self.change.action_type == 'REMOVE':
            subject_uids = self.change.parameters.get("conceptUids")
            if not isinstance(subject_uids, list) or not all(
                    isinstance(uid, str) for uid in subject_uids):
                raise ValueError(f"Invalid 'conceptUids' in parameters: {self.change.parameters}")

            await self._get_document_dao().remove_subjects(document_uid=document_uid,
                                                       subject_uids=subject_uids)
        elif self.change.action_type == 'ADD':
            subject_uid = self.change.parameters.get('uid')
            subject_uri = self.change.parameters.get('uri')
            subject_pref_labels = self.change.parameters.get('prefLabels', [])
            subject_alt_labels = self.change.parameters.get('altLabels', [])

            if not subject_uid or not isinstance(subject_uid, str) or subject_uid.strip() == "":
                raise ValueError(f"Invalid or empty 'uid' in "
                                 f"parameters of change {self.change.uid}")
            if not subject_uri or not isinstance(subject_uri, str) or subject_uri.strip() == "":
                raise ValueError(f"Invalid or empty 'uri' in "
                                 f"parameters of change {self.change.uid}")
            if (not subject_pref_labels or len(subject_pref_labels) == 0) and \
                    (not subject_alt_labels or len(subject_alt_labels) == 0):
                raise ValueError(f"Both 'prefLabels' and 'altLabels' are empty in "
                                 f"parameters of change {self.change.uid}")

            await self._get_document_dao().add_subject(document_uid=document_uid,
                                                       subject_uid=subject_uid,
                                                       subject_uri=subject_uri,
                                                       subject_pref_labels=subject_pref_labels,
                                                       subject_alt_labels=subject_alt_labels)

    def _get_document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        return cast(DocumentDAO, factory.get_dao(Document))

    def _get_dao_factory(self):
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
