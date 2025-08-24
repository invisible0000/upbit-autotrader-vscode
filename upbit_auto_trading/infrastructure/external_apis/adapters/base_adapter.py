"""
거래소별 어댑터 베이스 클래스

각 거래소의 특화된 로직을 격리하고 표준화된 인터페이스 제공
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from datetime import datetime

from ..core.data_models import (
    StandardTicker, StandardOrderbook, StandardCandle, StandardTrade,
    ExchangeMetadata
)


class ExchangeAdapter(ABC):
    """거래소별 어댑터 베이스 클래스"""

    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.metadata = ExchangeMetadata(exchange_name)

    # ================================================================
    # 심볼 및 파라미터 변환
    # ================================================================

    @abstractmethod
    def normalize_symbol_format(self, symbol: str) -> str:
        """거래소별 심볼 형식으로 변환"""
        pass

    @abstractmethod
    def build_batch_params(self, symbols: List[str], endpoint: str) -> Dict[str, Any]:
        """배치 요청용 파라미터 구성"""
        pass

    @abstractmethod
    def build_single_params(self, symbol: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """단일 요청용 파라미터 구성"""
        pass

    # ================================================================
    # 응답 데이터 파싱 및 표준화
    # ================================================================

    @abstractmethod
    def parse_ticker_response(self, raw_data: List[Dict[str, Any]]) -> List[StandardTicker]:
        """티커 응답을 표준 형식으로 변환"""
        pass

    @abstractmethod
    def parse_orderbook_response(self, raw_data: List[Dict[str, Any]]) -> List[StandardOrderbook]:
        """호가 응답을 표준 형식으로 변환"""
        pass

    @abstractmethod
    def parse_candle_response(self, raw_data: List[Dict[str, Any]],
                              symbol: str, timeframe: str) -> List[StandardCandle]:
        """캔들 응답을 표준 형식으로 변환"""
        pass

    @abstractmethod
    def parse_trade_response(self, raw_data: List[Dict[str, Any]],
                             symbol: str) -> List[StandardTrade]:
        """체결 응답을 표준 형식으로 변환"""
        pass

    # ================================================================
    # 에러 처리
    # ================================================================

    @abstractmethod
    def parse_error_response(self, response_data: Any, status_code: int) -> str:
        """에러 응답 파싱"""
        pass

    # ================================================================
    # 헬퍼 메서드들
    # ================================================================

    def supports_batch(self, endpoint: str) -> bool:
        """해당 엔드포인트에서 배치 지원 여부"""
        return self.metadata.get_batch_support(endpoint)

    def get_max_batch_size(self, endpoint: str) -> int:
        """최대 배치 크기"""
        return self.metadata.get_max_batch_size(endpoint)

    def get_base_url(self) -> str:
        """기본 URL"""
        return self.metadata.get_base_url()

    def _safe_decimal(self, value: Any) -> Decimal:
        """안전한 Decimal 변환"""
        if value is None:
            return Decimal('0')
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return Decimal('0')

    def _safe_datetime(self, timestamp: Any) -> datetime:
        """안전한 datetime 변환"""
        if isinstance(timestamp, datetime):
            return timestamp

        try:
            if isinstance(timestamp, (int, float)):
                # 밀리초 타임스탬프인지 확인
                if timestamp > 1e12:  # 밀리초
                    return datetime.fromtimestamp(timestamp / 1000)
                else:  # 초
                    return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # ISO 형식 파싱 시도
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, OSError):
            pass

        return datetime.now()


# ================================================================
# 범용 응답 변환 유틸리티
# ================================================================

class ResponseNormalizer:
    """거래소별 응답을 표준화하는 유틸리티"""

    @staticmethod
    def normalize_to_dict(data: List[Any], symbols: List[str],
                          key_field: str = 'symbol') -> Dict[str, Any]:
        """
        List 응답을 Dict 형태로 변환

        배열 데이터(캔들, 체결)는 심볼별 리스트로 그룹화하고,
        단일 데이터(티커, 호가)는 심볼별 객체로 매핑합니다.
        """
        if not isinstance(data, list):
            return {}

        # 배열 데이터인지 확인 (캔들, 체결 등)
        # 캔들: candle_date_time 필드 존재
        # 체결: sequential_id 필드 존재 (업비트 체결 데이터 고유 필드)
        is_array_data = any('candle_date_time' in str(item) or 'sequential_id' in str(item)
                            for item in data if isinstance(item, dict))

        result = {}

        if is_array_data:
            # 배열 데이터: 심볼별로 리스트 그룹화
            for symbol in symbols:
                result[symbol] = []

            for item in data:
                if isinstance(item, dict):
                    # market 필드로 심볼 추출 (업비트 표준)
                    key = item.get('market') or item.get(key_field)
                    if key and key in result:
                        result[key].append(item)
                    elif key:
                        # 새로운 심볼인 경우 리스트 생성
                        if key not in result:
                            result[key] = []
                        result[key].append(item)
        else:
            # 단일 데이터: 기존 로직 유지
            for item in data:
                if isinstance(item, dict):
                    key = item.get('market') or item.get(key_field)
                    if key:
                        result[key] = item
                elif hasattr(item, key_field):
                    # 객체인 경우 (StandardTicker 등)
                    key = getattr(item, key_field)
                    if key:
                        result[key] = item
                elif hasattr(item, 'symbol'):
                    # 기본적으로 symbol 속성 확인
                    key = getattr(item, 'symbol')
                    if key:
                        result[key] = item

            # 요청한 심볼 중 누락된 것들은 빈 dict로 추가
            for symbol in symbols:
                if symbol not in result:
                    result[symbol] = {}

        return result

    @staticmethod
    def create_unified_response(data: Dict[str, Any],
                                symbols: List[str],
                                endpoint: str,
                                exchange: str) -> Dict[str, Any]:
        """통합 응답 형식 생성"""
        return {
            "success": True,
            "data": data,
            "metadata": {
                "request_symbols": symbols,
                "response_count": len(data),
                "missing_symbols": [s for s in symbols if s not in data or not data[s]],
                "timestamp": datetime.now().isoformat(),
                "endpoint": endpoint,
                "exchange": exchange,
                "data_type": ResponseNormalizer._extract_data_type(endpoint)
            }
        }

    @staticmethod
    def _extract_data_type(endpoint: str) -> str:
        """엔드포인트에서 데이터 타입 추출"""
        if '/ticker' in endpoint:
            return 'ticker'
        elif '/orderbook' in endpoint:
            return 'orderbook'
        elif '/candle' in endpoint:
            return 'candle'
        elif '/trade' in endpoint:
            return 'trade'
        elif '/market' in endpoint:
            return 'market'
        else:
            return 'unknown'


class InputTypeHandler:
    """입력 타입 처리 유틸리티"""

    @staticmethod
    def normalize_symbol_input(symbols: Union[str, List[str]]) -> tuple[List[str], bool]:
        """심볼 입력을 정규화하고 원본 타입 기억"""
        if isinstance(symbols, str):
            return [symbols], True
        elif isinstance(symbols, list):
            return symbols, False
        else:
            raise ValueError(f"지원하지 않는 입력 타입: {type(symbols)}")

    @staticmethod
    def format_output(data: Dict[str, Any], was_single_input: bool,
                      single_symbol: Optional[str] = None) -> Any:
        """
        Dict 통일을 위한 출력 형태 변환

        단일/복수 요청 모두 Dict 형태로 통일하여
        일관된 접근 패턴을 제공합니다.
        """
        # Dict 통일: 단일 요청도 Dict 형태 유지
        return data
