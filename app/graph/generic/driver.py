from abc import ABC, abstractmethod


class Driver(ABC):
    """
    Abstract class for backend drivers
    """

    @abstractmethod
    async def _session(self):
        pass
