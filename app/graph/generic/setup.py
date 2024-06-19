from abc import ABC, abstractmethod
from typing import Generic

from app.graph.generic.driver_type import DriverType


class Setup(ABC, Generic[DriverType]):

    def __init__(self, driver: DriverType):
        self.driver: DriverType = driver

    @abstractmethod
    def run(self):
        pass
