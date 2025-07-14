from abc import ABC, abstractmethod

from app.models.change import Change


class AbstractChangeProcessor(ABC):
    """
    Abstract base class for all change processors.
    Implementations must define how to apply a Change.
    """

    def __init__(self, change: Change):
        self.change = change

    @abstractmethod
    async def apply(self) -> None:
        """
        Apply the change to the graph.
        Should raise ValueError or DatabaseError on failure.
        """
