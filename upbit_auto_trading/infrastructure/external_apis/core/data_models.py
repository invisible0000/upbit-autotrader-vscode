"""
거래소 중립적 공통 데이터 모델

모든 거래소가 공통으로 사용하는 표준화된 데이터 구조
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal


@dataclass
class StandardTicker:
    """표준화된 티커 데이터"""
    symbol: str                    # 심볼 (거래소별 형식 유지)
    price: Decimal                 # 현재가
    price_change: Decimal          # 가격 변화량
    price_change_percent: Decimal  # 가격 변화율 (%)
    volume_24h: Decimal           # 24시간 거래량
    volume_value_24h: Decimal     # 24시간 거래대금
    high_24h: Decimal             # 24시간 최고가
    low_24h: Decimal              # 24시간 최저가
    timestamp: datetime           # 타임스탬프
    exchange: str                 # 거래소명
    raw_data: Dict[str, Any]      # 원본 데이터 (디버깅용)


@dataclass
class StandardOrderbook:
    """표준화된 호가 데이터"""
    symbol: str
    bids: List[Dict[str, Decimal]]  # 매수 호가 [{'price': Decimal, 'size': Decimal}]
    asks: List[Dict[str, Decimal]]  # 매도 호가
    timestamp: datetime
    exchange: str
    raw_data: Dict[str, Any]


@dataclass
class StandardCandle:
    """표준화된 캔들 데이터"""
    symbol: str
    timeframe: str                # '1m', '5m', '1h', '1d' 등
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    timestamp: datetime
    exchange: str
    raw_data: Dict[str, Any]


@dataclass
class StandardTrade:
    """표준화된 체결 데이터"""
    symbol: str
    price: Decimal
    size: Decimal
    side: str                     # 'buy' | 'sell'
    timestamp: datetime
    trade_id: str
    exchange: str
    raw_data: Dict[str, Any]


@dataclass
class ApiResponse:
    """표준 API 응답 래퍼"""
    status_code: int
    data: Any
    headers: Dict[str, str]
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    exchange: Optional[str] = None


@dataclass
class UnifiedResponse:
    """통합 응답 형식 - 거래소 중립적"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    exchange: Optional[str] = None

    def get(self) -> Any:
        """원본 입력 형태에 맞는 응답 반환"""
        return self.data

    def get_single(self, symbol: str) -> Any:
        """단일 심볼 데이터 반환"""
        return self.data.get(symbol, {})

    def get_all(self) -> Dict[str, Any]:
        """전체 Dict 데이터 반환"""
        return self.data


class ExchangeMetadata:
    """거래소별 메타데이터"""

    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """거래소별 메타데이터 로드"""
        metadata_map = {
            'upbit': {
                'base_url': 'https://api.upbit.com/v1',
                'symbol_format': 'BASE-QUOTE',  # KRW-BTC
                'symbol_separator': '-',
                'batch_support': {
                    'ticker': True,
                    'orderbook': True,
                    'candle': False,
                    'trade': False
                },
                'max_batch_size': {
                    'ticker': 100,
                    'orderbook': 100
                },
                'rate_limits': {
                    'public': {'rps': 10, 'rpm': 600},
                    'private': {'rps': 8, 'rpm': 200}
                },
                'field_mapping': {
                    'symbol': 'market',
                    'price': 'trade_price',
                    'volume': 'acc_trade_volume_24h'
                }
            },
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'symbol_format': 'BASEQUOTE',   # BTCUSDT
                'symbol_separator': '',
                'batch_support': {
                    'ticker': True,
                    'orderbook': False,
                    'candle': False,
                    'trade': False
                },
                'max_batch_size': {
                    'ticker': 100
                },
                'rate_limits': {
                    'public': {'rps': 20, 'rpm': 1200},
                    'private': {'rps': 10, 'rpm': 600}
                },
                'field_mapping': {
                    'symbol': 'symbol',
                    'price': 'price',
                    'volume': 'volume'
                }
            }
        }
        return metadata_map.get(self.exchange_name, {})

    def get_base_url(self) -> str:
        return self._metadata.get('base_url', '')

    def get_symbol_format(self) -> str:
        return self._metadata.get('symbol_format', '')

    def get_batch_support(self, endpoint: str) -> bool:
        # 엔드포인트에서 데이터 타입 추출
        data_type = self._extract_data_type_from_endpoint(endpoint)
        return self._metadata.get('batch_support', {}).get(data_type, False)

    def get_max_batch_size(self, endpoint: str) -> int:
        # 엔드포인트에서 데이터 타입 추출
        data_type = self._extract_data_type_from_endpoint(endpoint)
        return self._metadata.get('max_batch_size', {}).get(data_type, 1)

    def _extract_data_type_from_endpoint(self, endpoint: str) -> str:
        """엔드포인트에서 데이터 타입 추출"""
        if '/ticker' in endpoint:
            return 'ticker'
        elif '/orderbook' in endpoint:
            return 'orderbook'
        elif '/candle' in endpoint:
            return 'candle'
        elif '/trade' in endpoint:
            return 'trade'
        else:
            return 'unknown'

    def get_rate_limits(self, api_type: str) -> Dict[str, int]:
        return self._metadata.get('rate_limits', {}).get(api_type, {'rps': 10, 'rpm': 600})

    def get_field_mapping(self, field: str) -> str:
        return self._metadata.get('field_mapping', {}).get(field, field)


# ================================================================
# 거래소별 예외 클래스들
# ================================================================

class ExchangeApiError(Exception):
    """거래소 API 기본 예외"""
    def __init__(self, message: str, status_code: Optional[int] = None, exchange: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.exchange = exchange


class AuthenticationError(ExchangeApiError):
    """인증 오류"""
    pass


class RateLimitError(ExchangeApiError):
    """Rate Limit 오류"""
    pass


class BatchSizeError(ExchangeApiError):
    """배치 크기 초과 오류"""
    pass


class SymbolNotFoundError(ExchangeApiError):
    """심볼을 찾을 수 없음"""
    pass


class ExchangeMaintenanceError(ExchangeApiError):
    """거래소 점검 중"""
    pass
