from abc import abstractmethod, ABC
from typing import Type

from pydantic import BaseModel

from app.graph.generic.dao import DAO
from app.graph.generic.setup import Setup


class DAOFactory(ABC):

    @abstractmethod
    def get_dao(self, object_type: Type[BaseModel]) -> DAO:
        pass

    @abstractmethod
    def get_setup(self) -> Setup:
        pass