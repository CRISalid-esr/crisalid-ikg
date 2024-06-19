from enum import Enum
from typing import TypeVar

from app.graph.generic.driver import Driver

DriverType = TypeVar("DriverType", bound=Driver)
