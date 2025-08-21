"""
업비트 WebSocket 메시지 통합 파서

업비트 공식 문서의 7가지 메시지 타입을 모두 지원:
1. ticker (현재가) - 공개
2. trade (체결) - 공개
3. orderbook (호가) - 공개
4. candle (캔들) - 공개
5. myOrder (내 주문) - 프라이빗
6. myAsset (내 자산) - 프라이빗
7. subscription (구독 관리) - 공개

https://docs.upbit.com/kr/reference/#websocket
"""

from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from decimal import Decimal
import json

from upbit_auto_trading.infrastructure.logging import create_component_logger


class UpbitMessageType(Enum):
    """업비트 WebSocket 메시지 타입 (공식 문서 기준)"""
    # 공개 메시지
    TICKER = "ticker"           # 현재가
    TRADE = "trade"             # 체결
    ORDERBOOK = "orderbook"     # 호가
    CANDLE = "candle"           # 캔들 (1, 3, 5, 10, 15, 30, 60, 240분)

    # 프라이빗 메시지 (API 키 필요)
    MY_ORDER = "myOrder"        # 내 주문
    MY_ASSET = "myAsset"        # 내 자산

    # 시스템 메시지
    SUBSCRIPTION = "subscription"  # 구독 관리
    ERROR = "error"             # 에러
    UNKNOWN = "unknown"         # 알 수 없는 타입


@dataclass(frozen=True)
class ParsedMessage:
    """파싱된 업비트 메시지 통합 구조"""
    type: UpbitMessageType
    market: str
    timestamp: datetime
    data: Dict[str, Any]
    raw_data: str

    # 공통 필드들 (타입별로 다름)
    price: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    change_rate: Optional[Decimal] = None

    # 메타데이터
    is_private: bool = False
    requires_auth: bool = False


class UpbitMessageParser:
    """업비트 WebSocket 메시지 통합 파서"""

    def __init__(self):
        self.logger = create_component_logger("UpbitMessageParser")

        # 타입별 필드 매핑 (업비트 공식 문서 기준)
        self._type_field_map = {
            UpbitMessageType.TICKER: {
                'price_field': 'trade_price',
                'volume_field': 'acc_trade_volume',
                'change_rate_field': 'signed_change_rate',
                'market_field': 'code'
            },
            UpbitMessageType.TRADE: {
                'price_field': 'trade_price',
                'volume_field': 'trade_volume',
                'change_rate_field': None,
                'market_field': 'code'
            },
            UpbitMessageType.ORDERBOOK: {
                'price_field': None,  # 호가는 여러 가격
                'volume_field': None,  # 호가는 여러 수량
                'change_rate_field': None,
                'market_field': 'code'
            },
            UpbitMessageType.CANDLE: {
                'price_field': 'trade_price',
                'volume_field': 'candle_acc_trade_volume',
                'change_rate_field': None,
                'market_field': 'code'
            },
            UpbitMessageType.MY_ORDER: {
                'price_field': 'price',
                'volume_field': 'volume',
                'change_rate_field': None,
                'market_field': 'market'
            },
            UpbitMessageType.MY_ASSET: {
                'price_field': 'avg_buy_price',
                'volume_field': 'balance',
                'change_rate_field': None,
                'market_field': 'currency'
            }
        }

    def parse_message(self, raw_message: Union[str, bytes]) -> Optional[ParsedMessage]:
        """메시지 파싱 (모든 타입 지원)"""
        try:
            # JSON 파싱
            if isinstance(raw_message, bytes):
                raw_str = raw_message.decode('utf-8')
            else:
                raw_str = raw_message

            data = json.loads(raw_str)

            # 메시지 타입 식별
            message_type = self._identify_message_type(data)
            if message_type == UpbitMessageType.UNKNOWN:
                self.logger.debug(f"알 수 없는 메시지 타입: {list(data.keys())[:10]}")
                return None

            # 시스템 메시지 처리
            if message_type in [UpbitMessageType.ERROR, UpbitMessageType.SUBSCRIPTION]:
                return self._parse_system_message(message_type, data, raw_str)

            # 시장 데이터 메시지 파싱
            return self._parse_market_message(message_type, data, raw_str)

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패: {e}")
            return None
        except Exception as e:
            self.logger.error(f"메시지 파싱 오류: {e}")
            return None

    def _identify_message_type(self, data: Dict[str, Any]) -> UpbitMessageType:
        """메시지 타입 식별 (업비트 공식 문서 기준)"""

        # 명시적 타입 필드 확인
        if 'type' in data:
            type_str = data['type']
            try:
                return UpbitMessageType(type_str)
            except ValueError:
                pass

        # 에러 메시지 확인
        if 'error' in data or 'message' in data:
            return UpbitMessageType.ERROR

        # 구독 관리 메시지 확인
        if 'status' in data and 'subscriptions' in data:
            return UpbitMessageType.SUBSCRIPTION

        # 필드 패턴으로 타입 추론
        if self._is_ticker_message(data):
            return UpbitMessageType.TICKER
        elif self._is_trade_message(data):
            return UpbitMessageType.TRADE
        elif self._is_orderbook_message(data):
            return UpbitMessageType.ORDERBOOK
        elif self._is_candle_message(data):
            return UpbitMessageType.CANDLE
        elif self._is_my_order_message(data):
            return UpbitMessageType.MY_ORDER
        elif self._is_my_asset_message(data):
            return UpbitMessageType.MY_ASSET

        return UpbitMessageType.UNKNOWN

    def _is_ticker_message(self, data: Dict[str, Any]) -> bool:
        """현재가 메시지 판별"""
        required_fields = ['trade_price', 'change_rate', 'signed_change_rate', 'opening_price']
        return all(field in data for field in required_fields)

    def _is_trade_message(self, data: Dict[str, Any]) -> bool:
        """체결 메시지 판별"""
        required_fields = ['trade_price', 'trade_volume', 'ask_bid', 'sequential_id']
        return all(field in data for field in required_fields)

    def _is_orderbook_message(self, data: Dict[str, Any]) -> bool:
        """호가 메시지 판별"""
        return 'orderbook_units' in data and isinstance(data['orderbook_units'], list)

    def _is_candle_message(self, data: Dict[str, Any]) -> bool:
        """캔들 메시지 판별"""
        required_fields = ['opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']
        return all(field in data for field in required_fields)

    def _is_my_order_message(self, data: Dict[str, Any]) -> bool:
        """내 주문 메시지 판별"""
        required_fields = ['uuid', 'side', 'ord_type', 'state']
        return all(field in data for field in required_fields)

    def _is_my_asset_message(self, data: Dict[str, Any]) -> bool:
        """내 자산 메시지 판별"""
        required_fields = ['currency', 'balance', 'locked', 'avg_buy_price']
        return all(field in data for field in required_fields)

    def _parse_system_message(self, message_type: UpbitMessageType,
                              data: Dict[str, Any], raw_str: str) -> ParsedMessage:
        """시스템 메시지 파싱"""
        return ParsedMessage(
            type=message_type,
            market="SYSTEM",
            timestamp=datetime.now(),
            data=data,
            raw_data=raw_str,
            is_private=False,
            requires_auth=False
        )

    def _parse_market_message(self, message_type: UpbitMessageType,
                              data: Dict[str, Any], raw_str: str) -> ParsedMessage:
        """시장 데이터 메시지 파싱"""

        # 타입별 필드 매핑 가져오기
        field_map = self._type_field_map.get(message_type, {})

        # 마켓 정보 추출
        market_field = field_map.get('market_field', 'code')
        market = data.get(market_field, 'UNKNOWN')

        # 공통 필드 추출
        price = self._extract_decimal_field(data, field_map.get('price_field'))
        volume = self._extract_decimal_field(data, field_map.get('volume_field'))
        change_rate = self._extract_decimal_field(data, field_map.get('change_rate_field'))

        # 프라이빗 메시지 여부
        is_private = message_type in [UpbitMessageType.MY_ORDER, UpbitMessageType.MY_ASSET]

        return ParsedMessage(
            type=message_type,
            market=market,
            timestamp=datetime.now(),
            data=data,
            raw_data=raw_str,
            price=price,
            volume=volume,
            change_rate=change_rate,
            is_private=is_private,
            requires_auth=is_private
        )

    def _extract_decimal_field(self, data: Dict[str, Any], field_name: Optional[str]) -> Optional[Decimal]:
        """필드에서 Decimal 값 추출"""
        if not field_name or field_name not in data:
            return None

        try:
            value = data[field_name]
            if value is None:
                return None
            return Decimal(str(value))
        except Exception:
            return None

    def get_supported_types(self) -> List[UpbitMessageType]:
        """지원하는 메시지 타입 목록"""
        return [
            UpbitMessageType.TICKER,
            UpbitMessageType.TRADE,
            UpbitMessageType.ORDERBOOK,
            UpbitMessageType.CANDLE,
            UpbitMessageType.MY_ORDER,
            UpbitMessageType.MY_ASSET,
            UpbitMessageType.SUBSCRIPTION,
            UpbitMessageType.ERROR
        ]

    def get_public_types(self) -> List[UpbitMessageType]:
        """공개 메시지 타입 목록"""
        return [
            UpbitMessageType.TICKER,
            UpbitMessageType.TRADE,
            UpbitMessageType.ORDERBOOK,
            UpbitMessageType.CANDLE,
            UpbitMessageType.SUBSCRIPTION,
            UpbitMessageType.ERROR
        ]

    def get_private_types(self) -> List[UpbitMessageType]:
        """프라이빗 메시지 타입 목록"""
        return [
            UpbitMessageType.MY_ORDER,
            UpbitMessageType.MY_ASSET
        ]
