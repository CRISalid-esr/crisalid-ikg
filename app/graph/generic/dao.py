from abc import ABC
from typing import Generic

from app.graph.generic.driver_type import DriverType


class DAO(ABC, Generic[DriverType]):
    """
    Parent class for all DAO classes
    """

    def __init__(self, driver: DriverType):
        self.driver: DriverType = driver
