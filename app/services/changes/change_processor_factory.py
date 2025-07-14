from app.models.change import Change, TargetType
from app.services.changes.processors.abstract_change_processor import AbstractChangeProcessor
from app.services.changes.processors.document_subjects_change_processor import \
    DocumentSubjectsChangeProcessor


class ChangeProcessorFactory:
    """
    Factory class to create change processors based on the type of change.
    """

    @staticmethod
    def get_processor(change: Change) -> AbstractChangeProcessor:
        """
        Get the appropriate change processor based on the change's target type and path.
        :param change:
        :return:
        """
        if change.target_type == TargetType.DOCUMENT:
            if change.path == "subjects":
                return DocumentSubjectsChangeProcessor(change)

        raise ValueError(f"Unsupported change path '{change.path}' "
                         f"for target type '{change.target_type}'")
