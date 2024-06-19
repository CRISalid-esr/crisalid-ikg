from abc import ABC, abstractmethod


class Driver(ABC):

    @abstractmethod
    async def _session(self):
        pass
