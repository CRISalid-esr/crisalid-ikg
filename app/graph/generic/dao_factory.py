from abc import abstractmethod, ABC
from typing import Type

from pydantic import BaseModel

from app.graph.generic.dao import DAO
from app.graph.generic.setup import Setup


class DAOFactory(ABC):
    """
    Parent class for all DAOFactory classes
    """

    @abstractmethod
    def get_dao(self, object_type: Type[BaseModel] | None = None) -> DAO:
        """
        Get the DAO instance for the given object type and the concrete backend

        :param object_type: A particular Pydantic model
        :return: The DAO instance for the given object type
        """

    @abstractmethod
    def get_setup(self) -> Setup:
        """
        Get the Setup class instance for the concrete backend

        :return:
        """
