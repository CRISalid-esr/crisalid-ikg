from enum import Enum
from typing import Dict, List, TypeVar, Generic, Type

from app.models.source_records import SourceRecord
from app.services.documents.merge_strategies.abstract_merge_strategy import MergeStrategy
from app.services.documents.merge_strategies.global_richest_merge_strategy import \
    GlobalRichestMergeStrategy
from app.services.documents.merge_strategies.richest_by_field_merge_strategy import \
    RichestByFieldMergeStrategy
from app.services.documents.merge_strategies.source_order_merge_strategy import \
    SourceOrderMergeStrategy

T = TypeVar("T")


class MergeStrategyFactory(Generic[T]):
    """
    Factory to create merge strategy instances
    """

    class StrategyType(Enum):
        """
        Strategy types supported by the factory
        """
        GLOBAL_RICHEST = "global_richest"
        SOURCE_ORDER = "source_order"
        RICHEST_BY_FIELD = "richest_by_field"

    @staticmethod
    def create_strategy(strategy_type: StrategyType,
                        source_records: List[SourceRecord],
                        parameters: Dict,
                        document_class: Type[T],
                        ) -> MergeStrategy:
        """
        Create the appropriate merge strategy based on the strategy type
        :param strategy_type: The type of strategy (e.g., "global_richest", "source_order")
        :param source_records: List of source records
        :param parameters: Strategy parameters
        :param document_class: The pydantic class to instantiate
        :param textual_document_uid: The textual document uid
        :return: MergeStrategy instance
        """
        strategy_class = None
        if strategy_type == MergeStrategyFactory.StrategyType.GLOBAL_RICHEST:
            strategy_class = GlobalRichestMergeStrategy[T]
        elif strategy_type == MergeStrategyFactory[T].StrategyType.SOURCE_ORDER:
            strategy_class = SourceOrderMergeStrategy[T]
        elif strategy_type == MergeStrategyFactory.StrategyType.RICHEST_BY_FIELD:
            strategy_class = RichestByFieldMergeStrategy[T]
        if strategy_class is not None:
            return strategy_class(source_records=source_records,
                                  parameters=parameters,
                                  document_type=document_class)
        raise ValueError(f"Unknown strategy type: {strategy_type}")
