# file: app/services/changes/change_processor_factory.py
from app.models.change import Change, TargetType
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor
from app.services.changes.processors.document_merge_change_processor import \
    DocumentMergeChangeProcessor
from app.services.changes.processors.document_subjects_change_processor import (
    DocumentSubjectsChangeProcessor,
)


class ChangeProcessorFactory:
    """
    Factory class to create change processors based on the type of change.
    """

    @staticmethod
    def get_processor(change: Change) -> AbstractChangeProcessor:
        """
        Get the appropriate change processor based on the change's target type, path, and action.
        """
        if change.target_type == TargetType.DOCUMENT:
            if change.action_type == "MERGE":
                return DocumentMergeChangeProcessor(change)

            if change.path == "subjects":
                return DocumentSubjectsChangeProcessor(change)

        raise ValueError(
            f"Unsupported change routing (target_type={change.target_type}, "
            f"path={change.path}, action_type={getattr(change, 'action_type', None)})"
        )
