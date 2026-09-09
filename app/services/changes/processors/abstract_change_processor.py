from abc import ABC, abstractmethod
from typing import cast

from app.config import get_app_settings
from app.graph.generic.abstract_dao_factory import AbstractDAOFactory
from app.graph.neo4j.document_dao import DocumentDAO
from app.models.change import Change
from app.models.change_report import ChangeApplicationReport
from app.models.document import Document


class AbstractChangeProcessor(ABC):
    """
    Abstract base class for all change processors.
    Implementations must define how to apply a Change.
    """

    def __init__(self, change: Change):
        self.change = change

    @abstractmethod
    async def apply(self) -> ChangeApplicationReport:
        """
        Apply the change to the graph and return an application report
        (an empty report means a clean success).
        Should raise ValueError or DatabaseError on failure.
        """

    def _get_document_dao(self) -> DocumentDAO:
        factory = self._get_dao_factory()
        return cast(DocumentDAO, factory.get_dao(Document))

    @staticmethod
    def _get_dao_factory():
        settings = get_app_settings()
        return AbstractDAOFactory().get_dao_factory(settings.graph_db)
