"""
Smart Data Provider 입력 검증 로직
Core 모듈로 이동하여 메인 클래스와 함께 관리
"""
import re
from typing import List, Optional
from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("InputValidator")


class InputValidator:
    """
    Smart Data Provider 입력 검증 담당 클래스

    필요한 경우에만 사용하는 선택적 검증 기능
    (일반적으로는 마켓 API에서 받은 데이터를 사용하므로 검증 불필요)
    """

    @staticmethod
    def validate_symbol_format(symbol: str) -> bool:
        """
        심볼 형식 검증 (선택적 사용)

        Args:
            symbol: 검증할 심볼 (예: 'KRW-BTC')

        Returns:
            유효한 심볼이면 True, 아니면 False

        Note:
            마켓 API에서 받은 심볼은 검증할 필요 없음
            사용자 입력이나 외부 데이터 검증 시에만 사용
        """
        if not symbol or not isinstance(symbol, str):
            return False

        # 1. 기본 형식 검증 (KRW-BTC, USDT-BTC 등)
        if not re.match(r'^[A-Z]+-[A-Z0-9]+$', symbol):
            return False

        # 2. 길이 검증
        parts = symbol.split('-')
        if len(parts) != 2:
            return False

        base_currency, quote_currency = parts
        if len(base_currency) < 2 or len(base_currency) > 10:
            return False
        if len(quote_currency) < 2 or len(quote_currency) > 20:
            return False

        return True

    @staticmethod
    def validate_timeframe_format(timeframe: str) -> bool:
        """
        타임프레임 형식 검증 (선택적 사용)

        Args:
            timeframe: 검증할 타임프레임 (예: '1m', '5m', '1h')

        Returns:
            유효한 타임프레임이면 True, 아니면 False
        """
        if not timeframe or not isinstance(timeframe, str):
            return False

        # 업비트 지원 타임프레임 목록
        valid_timeframes = [
            '1m', '3m', '5m', '15m', '10m', '30m', '60m',
            '1h', '4h', '1d', '1w', '1M'
        ]

        return timeframe in valid_timeframes

    @staticmethod
    def validate_symbols_batch(symbols: List[str]) -> tuple[bool, Optional[str]]:
        """
        다중 심볼 배치 검증 (선택적 사용)

        Args:
            symbols: 심볼 리스트

        Returns:
            (유효성, 에러메시지)
        """
        if not symbols or not isinstance(symbols, list):
            return False, "심볼 리스트가 필요합니다"

        # 개별 심볼 검증 (필요한 경우에만)
        invalid_symbols = []
        for symbol in symbols:
            if not InputValidator.validate_symbol_format(symbol):
                invalid_symbols.append(symbol)

        if invalid_symbols:
            return False, f"유효하지 않은 심볼들: {', '.join(invalid_symbols)}"

        return True, None

    @staticmethod
    def validate_count_range(count: int, min_count: int = 1, max_count: int = 500) -> tuple[bool, Optional[str]]:
        """
        개수 범위 검증

        Args:
            count: 검증할 개수
            min_count: 최소값
            max_count: 최대값

        Returns:
            (유효성, 에러메시지)
        """
        if count < min_count or count > max_count:
            return False, f"개수는 {min_count}~{max_count} 범위여야 합니다. 입력값: {count}"

        return True, None
