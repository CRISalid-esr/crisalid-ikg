from abc import ABC
from enum import Enum
from typing import Generic

from app.graph.generic.driver_type import DriverType


class DAO(ABC, Generic[DriverType]):
    """
    Parent class for all DAO classes
    """
    class Status(Enum):
        """
        Status of the operation
        """
        CREATED = "CREATED"
        UPDATED = "UPDATED"
        DELETED = "DELETED"
        UNCHANGED = "UNCHANGED"

    def __init__(self, driver: DriverType):
        self.driver: DriverType = driver
