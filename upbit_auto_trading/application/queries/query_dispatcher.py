"""
Query Dispatcher 구현
Query와 Handler를 매핑하여 실행하는 중앙 디스패처
"""

from typing import Dict, Type, Any
import logging

from upbit_auto_trading.application.queries.handlers.base_query_handler import BaseQueryHandler


class QueryDispatcher:
    """Query와 Handler를 매핑하여 실행하는 디스패처"""

    def __init__(self):
        self._handlers: Dict[Type, BaseQueryHandler] = {}
        self._logger = logging.getLogger(__name__)

    def register_handler(self, query_type: Type, handler: BaseQueryHandler) -> None:
        """Query Handler 등록"""
        self._handlers[query_type] = handler
        self._logger.debug(f"Query Handler 등록: {query_type.__name__} -> {handler.__class__.__name__}")

    def dispatch(self, query: Any) -> Any:
        """Query 실행"""
        query_type = type(query)

        if query_type not in self._handlers:
            raise ValueError(f"등록되지 않은 Query 타입입니다: {query_type.__name__}")

        handler = self._handlers[query_type]

        try:
            self._logger.debug(f"Query 실행: {query_type.__name__}")
            result = handler.handle(query)
            self._logger.debug(f"Query 실행 완료: {query_type.__name__}")
            return result
        except Exception as e:
            self._logger.error(f"Query 실행 실패: {query_type.__name__} - {str(e)}")
            raise

    def get_registered_handlers(self) -> Dict[str, str]:
        """등록된 핸들러 목록 반환"""
        return {
            query_type.__name__: handler.__class__.__name__
            for query_type, handler in self._handlers.items()
        }
