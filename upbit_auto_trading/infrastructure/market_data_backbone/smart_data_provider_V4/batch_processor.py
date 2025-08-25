"""
배치 처리 엔진 - 다중 심볼 동시 처리

V4.0에서는 복잡한 요청 분할 대신
단순하고 효율적인 배치 처리를 제공
"""

from typing import List, Dict, Any, Union
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("BatchProcessor")


class BatchProcessor:
    """
    배치 처리 엔진
    - 다중 심볼 동시 처리
    - 단순한 배치 로직
    - 에러 처리 포함
    """

    def __init__(self):
        logger.info("BatchProcessor 초기화")

    async def process_symbols(self, symbols: Union[str, List[str]], processor_func, **kwargs) -> Dict[str, Any]:
        """
        심볼 배치 처리

        Args:
            symbols: 단일 심볼(str) 또는 다중 심볼(List[str])
            processor_func: 실제 처리 함수
            **kwargs: 추가 매개변수

        Returns:
            Dict[str, Any]: 처리 결과
        """

        # 1. 단일 심볼 처리
        if isinstance(symbols, str):
            logger.debug(f"단일 심볼 처리: {symbols}")
            return await processor_func(symbols, **kwargs)

        # 2. 다중 심볼 처리
        elif isinstance(symbols, list):
            logger.debug(f"다중 심볼 배치 처리: {len(symbols)}개")

            # SmartRouter는 이미 배치 처리를 지원하므로 그대로 전달
            return await processor_func(symbols, **kwargs)

        else:
            raise ValueError(f"지원하지 않는 심볼 타입: {type(symbols)}")

    def validate_symbols(self, symbols: Union[str, List[str]]) -> bool:
        """심볼 유효성 검증"""

        if isinstance(symbols, str):
            return bool(symbols and symbols.strip())

        elif isinstance(symbols, list):
            return len(symbols) > 0 and all(
                isinstance(symbol, str) and symbol.strip()
                for symbol in symbols
            )

        return False
