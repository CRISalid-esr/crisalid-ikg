from abc import ABC, abstractmethod
from typing import Generic

from app.graph.generic.driver_type import DriverType


class Setup(ABC, Generic[DriverType]):
    """
    Parent class for all setup classes
    """

    def __init__(self, driver: DriverType):
        self.driver: DriverType = driver

    @abstractmethod
    async def run(self) -> None:
        """
        Run the setup
        :return: None
        """
