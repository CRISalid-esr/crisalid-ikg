from abc import ABC, abstractmethod
from typing import List, Dict, TypeVar, Generic, Type

from app.models.source_records import SourceRecord

T = TypeVar("T")


class MergeStrategy(ABC, Generic[T]):
    """
    Abstract base class for merge strategies
    """

    def __init__(self, source_records: List[SourceRecord],
                 parameters: Dict,
                 document_type: Type[T]):
        """
        Constructor
        :param source_records: the source records to merge
        :param parameters: strategy parameters (from config)
        """
        self.source_records = source_records
        self.parameters = parameters
        self.document_type = document_type
        self.textual_document = None

    @abstractmethod
    def merge(self) -> T:
        """
        Merge source records into a document of type T
        :return: Merged document of type T
        """
