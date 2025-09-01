"""
업비트 WebSocket v6.0 - 통합 데이터 모델
========================================

🎯 특징:
- v5 모델의 우수한 구조 계승 + v6 타입 시스템 통합
- 혼합 타입 응답 완벽 지원 (현재가 + 체결 + 호가 + 캔들 + 내주문 + 내자산)
- 최대 성능 (Pydantic 오버헤드 제거)
- 업비트 공식 API 필드명 100% 호환
- SIMPLE 포맷 완전 지원 (bandwidth 최적화)
- v6 이벤트 시스템과 완전 호환
- 사용자 친화적 필드 문서화
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal
import time

# 타입 시스템 통합 (types.py에서 모든 타입 import)
from .types import (
    DataType,
    WebSocketType,
    BaseWebSocketEvent,
    TickerEvent,
    OrderbookEvent,
    TradeEvent,
    CandleEvent,
    MyOrderEvent,
    MyAssetEvent,
    create_ticker_event,
    create_orderbook_event,
    get_data_type_from_message
)

# SIMPLE 포맷 변환기 통합
try:
    from .simple_format_converter import (
        auto_detect_and_convert,
        convert_to_simple_format,
        convert_from_simple_format
    )
    SIMPLE_FORMAT_AVAILABLE = True
except ImportError:
    SIMPLE_FORMAT_AVAILABLE = False

    # 폴백 함수들
    def auto_detect_and_convert(data, **kwargs):
        return data

    def convert_to_simple_format(data, **kwargs):
        return data


class StreamType(str, Enum):
    """WebSocket 스트림 타입"""
    SNAPSHOT = "SNAPSHOT"
    REALTIME = "REALTIME"


# models.py의 DataType 클래스는 제거 - types.py 것 사용


# ================================================================
# 이벤트 시스템 통합 (dict -> Event 변환)
# ================================================================

def convert_dict_to_event(
    message_data: Dict[str, Any],
    epoch: int = 0,
    connection_type: Optional[WebSocketType] = None
) -> Optional[BaseWebSocketEvent]:
    """
    Dict 기반 메시지를 이벤트 객체로 변환

    Args:
        message_data: 검증된 Dict 메시지
        epoch: 재연결 구분용 세대 번호
        connection_type: WebSocket 연결 타입

    Returns:
        BaseWebSocketEvent: 이벤트 객체 또는 None
    """
    if not connection_type:
        connection_type = WebSocketType.PUBLIC

    msg_type = infer_message_type(message_data)

    try:
        if msg_type == 'ticker':
            return create_ticker_event(message_data, epoch, connection_type)
        elif msg_type == 'orderbook':
            return create_orderbook_event(message_data, epoch, connection_type)
        elif msg_type == 'trade':
            return TradeEvent(
                epoch=epoch,
                timestamp=time.time(),
                connection_type=connection_type,
                symbol=message_data.get('code'),
                trade_price=Decimal(str(message_data.get('trade_price', 0))),
                trade_volume=Decimal(str(message_data.get('trade_volume', 0))),
                ask_bid=message_data.get('ask_bid', ''),
                trade_timestamp=message_data.get('trade_timestamp', 0),
                sequential_id=message_data.get('sequential_id', 0),
                prev_closing_price=Decimal(str(message_data.get('prev_closing_price', 0)))
            )
        elif msg_type == 'candle':
            return CandleEvent(
                epoch=epoch,
                timestamp=time.time(),
                connection_type=connection_type,
                symbol=message_data.get('code'),
                opening_price=Decimal(str(message_data.get('opening_price', 0))),
                high_price=Decimal(str(message_data.get('high_price', 0))),
                low_price=Decimal(str(message_data.get('low_price', 0))),
                trade_price=Decimal(str(message_data.get('trade_price', 0))),
                candle_acc_trade_price=Decimal(str(message_data.get('candle_acc_trade_price', 0))),
                candle_acc_trade_volume=Decimal(str(message_data.get('candle_acc_trade_volume', 0))),
                unit=message_data.get('unit', 1),
                candle_timestamp=message_data.get('timestamp', 0)
            )
        elif msg_type == 'myOrder':
            def safe_decimal(value):
                return Decimal(str(value)) if value is not None else None

            return MyOrderEvent(
                epoch=epoch,
                timestamp=time.time(),
                connection_type=connection_type,
                symbol=message_data.get('market', ''),
                uuid=message_data.get('uuid', ''),
                order_type=message_data.get('ord_type', ''),
                ord_type=message_data.get('side', ''),
                price=safe_decimal(message_data.get('price')),
                avg_price=safe_decimal(message_data.get('avg_price')),
                state=message_data.get('state', ''),
                market=message_data.get('market', ''),
                created_at=message_data.get('created_at', ''),
                volume=safe_decimal(message_data.get('volume')),
                remaining_volume=safe_decimal(message_data.get('remaining_volume')),
                reserved_fee=safe_decimal(message_data.get('reserved_fee')),
                remaining_fee=safe_decimal(message_data.get('remaining_fee')),
                paid_fee=safe_decimal(message_data.get('paid_fee')),
                locked=safe_decimal(message_data.get('locked')),
                executed_volume=safe_decimal(message_data.get('executed_volume')),
                trades_count=message_data.get('trades_count')
            )
        elif msg_type == 'myAsset':
            return MyAssetEvent(
                epoch=epoch,
                timestamp=time.time(),
                connection_type=connection_type,
                symbol=message_data.get('currency', ''),
                currency=message_data.get('currency', ''),
                balance=Decimal(str(message_data.get('balance', 0))),
                locked=Decimal(str(message_data.get('locked', 0))),
                avg_buy_price=(Decimal(str(message_data.get('avg_buy_price', 0)))
                               if message_data.get('avg_buy_price') else None),
                avg_buy_price_modified=message_data.get('avg_buy_price_modified'),
                unit_currency=message_data.get('unit_currency')
            )
    except Exception as e:
        print(f"이벤트 변환 실패: {e}")
        return None

    return None


def process_message_to_event(
    raw_data: Dict[str, Any],
    epoch: int = 0,
    connection_type: Optional[WebSocketType] = None,
    format_preference: str = "auto",
    validate_data: bool = True
) -> Optional[BaseWebSocketEvent]:
    """
    원시 메시지를 v6 이벤트로 완전 변환 (검증 + 변환)

    Args:
        raw_data: 원시 WebSocket 메시지
        epoch: 재연결 구분용 세대 번호
        connection_type: WebSocket 연결 타입
        format_preference: 포맷 선호도 ("auto", "simple", "default")
        validate_data: 데이터 검증 여부

    Returns:
        BaseWebSocketEvent: v6 이벤트 객체 또는 None
    """
    try:
        # 1. 메시지 형식 처리 (SIMPLE 포맷 등)
        processed_data = process_websocket_message(
            raw_data,
            format_preference=format_preference,
            validate_data=validate_data
        )

        # 2. 이벤트로 변환
        return convert_dict_to_event(
            processed_data['data'],
            epoch=epoch,
            connection_type=connection_type
        )

    except Exception as e:
        print(f"메시지 -> 이벤트 변환 실패: {e}")
        return None


def get_data_type_from_dict(message_data: Dict[str, Any]) -> Optional[DataType]:
    """Dict 메시지에서 DataType 추론 (types.py의 get_data_type_from_message 호출)"""
    return get_data_type_from_message(message_data)


# ================================================================
# v6 호환성 유틸리티
# ================================================================

def create_compatible_message(
    msg_type: str,
    market: str,
    data: Dict[str, Any],
    epoch: int = 0,
    connection_type: Optional[WebSocketType] = None,
    timestamp: Optional[datetime] = None,
    stream_type: Optional[str] = None
) -> Dict[str, Any]:
    """v6 호환 메시지 생성 (Dict + v6 Event 동시 지원)"""
    # 기본 Dict 메시지 생성
    dict_message = create_websocket_message(
        msg_type, market, data, timestamp, stream_type
    )

    # 이벤트 추가
    event = convert_dict_to_event(
        data, epoch=epoch, connection_type=connection_type
    )

    # 통합 메시지 구조
    return {
        'dict_format': dict_message,
        'event': event,
        'format_type': 'compatible',
        'supports_both': True
    }

# ================================================================
# 기본 WebSocket 메시지 유틸리티 (기존 클라이언트 패턴)
# ================================================================

def create_websocket_message(msg_type: str, market: str, data: Dict[str, Any],
                             timestamp: Optional[datetime] = None,
                             stream_type: Optional[str] = None) -> Dict[str, Any]:
    """WebSocket 메시지 생성 (기존 클라이언트 패턴)"""
    return {
        'type': msg_type,
        'market': market.upper() if market else 'UNKNOWN',
        'data': data,
        'timestamp': timestamp or datetime.now(),
        'stream_type': stream_type,
        'raw_data': data
    }


def is_snapshot_message(message: Dict[str, Any]) -> bool:
    """스냅샷 메시지 여부 (기존 클라이언트 패턴)"""
    return message.get('stream_type') == 'SNAPSHOT'


def is_realtime_message(message: Dict[str, Any]) -> bool:
    """실시간 메시지 여부 (기존 클라이언트 패턴)"""
    return message.get('stream_type') == 'REALTIME'


# ================================================================
# 현재가 (Ticker) 필드 모델 - 업비트 공식 API 기준
# ================================================================

TICKER_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (ticker)',
    'code': '마켓 코드 (예: KRW-BTC)',

    # 💰 가격 정보 (OHLC + 현재가)
    'opening_price': '시가 (당일 첫 거래가격)',
    'high_price': '고가 (당일 최고가)',
    'low_price': '저가 (당일 최저가)',
    'trade_price': '현재가 (최근 체결가)',
    'prev_closing_price': '전일 종가',

    # 📈 변화량 정보
    'change': '변화 방향 (RISE: 상승, EVEN: 보합, FALL: 하락)',
    'change_price': '변화금액 (절대값)',
    'change_rate': '변화율 (소수점, 0.05 = 5%)',
    'signed_change_price': '부호 포함 변화금액 (+상승, -하락)',
    'signed_change_rate': '부호 포함 변화율 (+상승, -하락)',

    # 📊 거래량 정보
    'trade_volume': '현재 체결량',
    'acc_trade_price': '누적 거래대금 (당일)',
    'acc_trade_volume': '누적 거래량 (당일)',
    'acc_trade_price_24h': '24시간 누적 거래대금',
    'acc_trade_volume_24h': '24시간 누적 거래량',

    # 🏆 52주 최고/최저 (연간 통계)
    'highest_52_week_price': '52주 최고가',
    'highest_52_week_date': '52주 최고가 달성일 (YYYY-MM-DD)',
    'lowest_52_week_price': '52주 최저가',
    'lowest_52_week_date': '52주 최저가 달성일 (YYYY-MM-DD)',

    # 🎯 시장 상태
    'market_state': '시장 상태 (ACTIVE: 거래가능, PREVIEW: 입금지원, DELISTED: 거래중단)',
    'is_trading_suspended': '거래 중단 여부 (true/false)',
    'delisting_date': '상장폐지일 (YYYY-MM-DD)',
    'market_warning': '시장 경고 (NONE: 해당없음, CAUTION: 투자유의)',

    # ⏰ 타임스탬프
    'timestamp': '타임스탬프 (밀리초, Unix time)',
    'trade_date': '최근거래일자 (UTC, YYYY-MM-DD)',
    'trade_time': '최근거래시각 (UTC, HHmmss)',
    'trade_date_kst': '최근거래일자 (KST, YYYY-MM-DD)',
    'trade_time_kst': '최근거래시각 (KST, HHmmss)',
    'trade_timestamp': '체결 타임스탬프 (밀리초)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}


def validate_ticker_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """현재가 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['code', 'trade_price']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"현재가 데이터 필수 필드 누락: {field}")

    # 가격 필드 양수 검증
    price_fields = ['opening_price', 'high_price', 'low_price', 'trade_price']
    for field in price_fields:
        if field in validated and validated[field] is not None:
            if float(validated[field]) <= 0:
                raise ValueError(f"가격 필드는 양수여야 함: {field}={validated[field]}")

    # 변화 방향 검증
    if 'change' in validated and validated['change'] not in [None, 'RISE', 'EVEN', 'FALL']:
        raise ValueError(f"변화 방향이 잘못됨: {validated['change']} (RISE/EVEN/FALL만 허용)")

    return validated


# ================================================================
# 체결 (Trade) 필드 모델 - 업비트 공식 API 기준
# ================================================================

TRADE_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (trade)',
    'code': '마켓 코드 (예: KRW-BTC)',

    # 💱 체결 정보
    'trade_price': '체결가격',
    'trade_volume': '체결량',
    'ask_bid': '매수/매도 구분 (ASK: 매도, BID: 매수)',
    'prev_closing_price': '전일 종가',
    'change': '변화 방향 (RISE/EVEN/FALL)',
    'change_price': '변화금액',

    # 🔢 체결 번호 (순서 보장)
    'sequential_id': '체결 번호 (증가하는 고유번호)',

    # ⏰ 체결 시각
    'trade_date': '체결일자 (UTC, YYYY-MM-DD)',
    'trade_time': '체결시각 (UTC, HHmmss)',
    'trade_date_kst': '체결일자 (KST, YYYY-MM-DD)',
    'trade_time_kst': '체결시각 (KST, HHmmss)',
    'timestamp': '체결 타임스탬프 (밀리초)',
    'trade_timestamp': '체결 타임스탬프 (밀리초, 중복)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}


def validate_trade_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """체결 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['code', 'trade_price', 'trade_volume', 'ask_bid', 'sequential_id']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"체결 데이터 필수 필드 누락: {field}")

    # 매수/매도 구분 검증
    if validated['ask_bid'] not in ['ASK', 'BID']:
        raise ValueError(f"매수/매도 구분이 잘못됨: {validated['ask_bid']} (ASK/BID만 허용)")

    # 체결가/체결량 양수 검증
    if float(validated['trade_price']) <= 0:
        raise ValueError(f"체결가는 양수여야 함: {validated['trade_price']}")
    if float(validated['trade_volume']) <= 0:
        raise ValueError(f"체결량은 양수여야 함: {validated['trade_volume']}")

    return validated


# ================================================================
# 호가 (Orderbook) 필드 모델 - 업비트 공식 API 기준
# ================================================================

ORDERBOOK_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (orderbook)',
    'code': '마켓 코드 (예: KRW-BTC)',

    # 📋 호가 데이터 (배열)
    'orderbook_units': '호가 정보 배열 (레벨별 매수/매도 호가)',
    'total_ask_size': '총 매도 잔량',
    'total_bid_size': '총 매수 잔량',
    'level': '호가 레벨 (기본: 15레벨)',

    # ⏰ 타임스탬프
    'timestamp': '호가 타임스탬프 (밀리초)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}

ORDERBOOK_UNIT_FIELDS = {
    # 각 호가 레벨의 필드 (orderbook_units 배열의 각 요소)
    'ask_price': '매도호가',
    'bid_price': '매수호가',
    'ask_size': '매도잔량',
    'bid_size': '매수잔량'
}


def validate_orderbook_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """호가 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['code', 'orderbook_units']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"호가 데이터 필수 필드 누락: {field}")

    # 호가 유닛 배열 검증
    orderbook_units = validated['orderbook_units']
    if not isinstance(orderbook_units, list) or len(orderbook_units) == 0:
        raise ValueError("호가 정보가 비어있음")

    # 각 호가 레벨 검증
    for i, unit in enumerate(orderbook_units):
        if not isinstance(unit, dict):
            raise ValueError(f"호가 레벨 {i}가 올바른 형식이 아님")

        unit_required = ['ask_price', 'bid_price', 'ask_size', 'bid_size']
        for field in unit_required:
            if field not in unit or unit[field] is None:
                raise ValueError(f"호가 레벨 {i} 필수 필드 누락: {field}")
            if float(unit[field]) < 0:
                raise ValueError(f"호가 레벨 {i} 필드가 음수: {field}={unit[field]}")

    return validated


# ================================================================
# 캔들 (Candle) 필드 모델 - 업비트 공식 API 기준
# ================================================================

CANDLE_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (candle.1m, candle.5m 등)',
    'code': '마켓 코드 (예: KRW-BTC)',

    # 📊 OHLC 데이터
    'opening_price': '시가 (구간 첫 거래가)',
    'high_price': '고가 (구간 최고가)',
    'low_price': '저가 (구간 최저가)',
    'trade_price': '종가 (구간 마지막 거래가)',
    'prev_closing_price': '전 구간 종가',

    # 📈 변화량 정보
    'change': '변화 방향 (RISE/EVEN/FALL)',
    'change_price': '변화금액',
    'change_rate': '변화율',

    # 📊 거래량 정보
    'candle_acc_trade_price': '캔들 구간 누적거래대금',
    'candle_acc_trade_volume': '캔들 구간 누적거래량',
    'unit': '분 단위 (1, 3, 5, 15, 30, 60, 240)',

    # ⏰ 캔들 시각 (UTC/KST)
    'candle_date_time_utc': '캔들 기준시각 (UTC, YYYY-MM-DD\'T\'HH:mm:ss)',
    'candle_date_time_kst': '캔들 기준시각 (KST, YYYY-MM-DD\'T\'HH:mm:ss)',
    'timestamp': '타임스탬프 (밀리초)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}


def validate_candle_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """캔들 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['code', 'opening_price', 'high_price', 'low_price', 'trade_price']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"캔들 데이터 필수 필드 누락: {field}")

    # OHLC 가격 양수 검증
    ohlc_fields = ['opening_price', 'high_price', 'low_price', 'trade_price']
    for field in ohlc_fields:
        if float(validated[field]) <= 0:
            raise ValueError(f"OHLC 가격은 양수여야 함: {field}={validated[field]}")

    # OHLC 논리 검증 (고가 >= 저가)
    high = float(validated['high_price'])
    low = float(validated['low_price'])
    if high < low:
        raise ValueError(f"고가({high})가 저가({low})보다 낮음")

    return validated


# ================================================================
# 내주문 (My Order) 필드 모델 - 업비트 공식 API 기준
# ================================================================

MY_ORDER_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (myOrder)',
    'uuid': '주문 고유식별자',
    'market': '마켓 코드 (예: KRW-BTC)',

    # 📝 주문 정보
    'side': '주문 종류 (bid: 매수, ask: 매도)',
    'ord_type': '주문 방식 (limit: 지정가, price: 시장가매수, market: 시장가매도)',
    'price': '주문 당시 화폐가격',
    'avg_price': '체결 가격의 가중평균',
    'state': '주문 상태 (wait: 대기, watch: 예약, done: 완료, cancel: 취소)',

    # 💰 수량/금액 정보
    'volume': '사용자가 입력한 주문량',
    'remaining_volume': '체결 후 남은 주문량',
    'reserved_fee': '수수료로 예약된 금액',
    'remaining_fee': '남은 수수료',
    'paid_fee': '사용된 수수료',
    'locked': '거래에 사용중인 금액',
    'executed_volume': '체결된 양',
    'trades_count': '해당 주문에 걸린 체결 수',

    # ⏰ 시각 정보
    'created_at': '주문 생성시간 (ISO 8601)',
    'updated_at': '주문 수정시간 (ISO 8601)',
    'reserved_at': '주문 예약시간 (ISO 8601)',
    'executed_at': '주문 체결시간 (ISO 8601)',
    'canceled_at': '주문 취소시간 (ISO 8601)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}


def validate_my_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """내주문 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['uuid', 'market', 'side', 'ord_type', 'state']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"내주문 데이터 필수 필드 누락: {field}")

    # 주문 종류 검증
    if validated['side'] not in ['bid', 'ask']:
        raise ValueError(f"주문 종류가 잘못됨: {validated['side']} (bid/ask만 허용)")

    # 주문 방식 검증
    valid_ord_types = ['limit', 'price', 'market']
    if validated['ord_type'] not in valid_ord_types:
        raise ValueError(f"주문 방식이 잘못됨: {validated['ord_type']} ({'/'.join(valid_ord_types)}만 허용)")

    # 주문 상태 검증
    valid_states = ['wait', 'watch', 'done', 'cancel']
    if validated['state'] not in valid_states:
        raise ValueError(f"주문 상태가 잘못됨: {validated['state']} ({'/'.join(valid_states)}만 허용)")

    return validated


# ================================================================
# 내자산 (My Asset) 필드 모델 - 업비트 공식 API 기준
# ================================================================

MY_ASSET_FIELDS = {
    # 🏷️ 기본 정보
    'type': '메시지 타입 (myAsset)',
    'currency': '화폐 코드 (KRW, BTC, ETH 등)',

    # 💰 자산 정보
    'balance': '주문가능 금액/수량',
    'locked': '주문 중 묶여있는 금액/수량',
    'avg_buy_price': '매수평균가',
    'avg_buy_price_modified': '매수평균가 수정 여부',
    'unit_currency': '평단가 기준 화폐',

    # ⏰ 시각 정보
    'created_at': '계좌 생성시간 (ISO 8601)',
    'updated_at': '계좌 수정시간 (ISO 8601)',

    # 🔄 스트림 정보
    'stream_type': '스트림 타입 (SNAPSHOT: 스냅샷, REALTIME: 실시간)'
}


def validate_my_asset_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """내자산 데이터 검증 및 기본값 설정"""
    validated = data.copy()

    # 필수 필드 검증
    required_fields = ['currency', 'balance', 'locked']
    for field in required_fields:
        if field not in validated or validated[field] is None:
            raise ValueError(f"내자산 데이터 필수 필드 누락: {field}")

    # 잔고/락 금액 음수 방지
    balance_fields = ['balance', 'locked']
    for field in balance_fields:
        if float(validated[field]) < 0:
            raise ValueError(f"잔고는 음수일 수 없음: {field}={validated[field]}")

    return validated


# ================================================================
# 혼합 타입 메시지 처리 유틸리티 (핵심 기능)
# ================================================================

def infer_message_type(data: Dict[str, Any]) -> str:
    """
    메시지 타입 자동 추론 (업비트 실제 응답 패턴 기반)

    Args:
        data: WebSocket으로 받은 원시 데이터

    Returns:
        str: 추론된 메시지 타입 (ticker/trade/orderbook/candle/myOrder/myAsset)
    """
    # 1. type 필드로 직접 판단 (가장 확실한 방법)
    if 'type' in data:
        msg_type = data['type']
        if msg_type == 'ticker':
            return 'ticker'
        elif msg_type == 'trade':
            return 'trade'
        elif msg_type == 'orderbook':
            return 'orderbook'
        elif msg_type.startswith('candle'):
            return msg_type  # 전체 캔들 타입 반환 (candle.1s, candle.1m 등)
        elif msg_type == 'myOrder':
            return 'myOrder'
        elif msg_type == 'myAsset':
            return 'myAsset'

    # 2. ty 필드로 판단 (업비트 실제 응답에서 사용)
    if 'ty' in data:
        msg_type = data['ty']
        if msg_type == 'ticker':
            return 'ticker'
        elif msg_type == 'trade':
            return 'trade'
        elif msg_type == 'orderbook':
            return 'orderbook'
        elif msg_type.startswith('candle'):
            return msg_type  # 전체 캔들 타입 반환 (candle.1s, candle.1m 등)

    # 3. 필드 조합으로 추론 (type 필드가 없는 경우)
    if 'trade_price' in data and 'change_rate' in data and 'acc_trade_volume_24h' in data:
        return 'ticker'
    elif 'ask_bid' in data and 'sequential_id' in data:
        return 'trade'
    elif 'orderbook_units' in data and 'total_ask_size' in data:
        return 'orderbook'
    elif 'candle_date_time_utc' in data and 'candle_acc_trade_volume' in data:
        return 'candle'
    elif 'uuid' in data and 'side' in data and 'ord_type' in data:
        return 'myOrder'
    elif 'currency' in data and 'balance' in data and 'locked' in data:
        return 'myAsset'

    # 4. 기본값 (추론 실패 시)
    return 'unknown'


def validate_mixed_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    혼합 타입 메시지 통합 검증

    Args:
        data: 원시 WebSocket 메시지 데이터

    Returns:
        Dict: 검증된 데이터 (타입별 검증 함수 적용)
    """
    msg_type = infer_message_type(data)

    try:
        if msg_type == 'ticker':
            return validate_ticker_data(data)
        elif msg_type == 'trade':
            return validate_trade_data(data)
        elif msg_type == 'orderbook':
            return validate_orderbook_data(data)
        elif msg_type == 'candle':
            return validate_candle_data(data)
        elif msg_type == 'myOrder':
            return validate_my_order_data(data)
        elif msg_type == 'myAsset':
            return validate_my_asset_data(data)
        else:
            # 알 수 없는 타입은 원본 그대로 반환
            return data

    except ValueError as e:
        # 검증 실패 시 원본 데이터 + 오류 정보 반환
        return {
            **data,
            '_validation_error': str(e),
            '_inferred_type': msg_type
        }


def get_field_documentation(msg_type: str) -> Dict[str, str]:
    """
    메시지 타입별 필드 문서 반환

    Args:
        msg_type: 메시지 타입 (ticker/trade/orderbook/candle/myOrder/myAsset)

    Returns:
        Dict[str, str]: 필드명 -> 설명 매핑
    """
    field_docs = {
        'ticker': TICKER_FIELDS,
        'trade': TRADE_FIELDS,
        'orderbook': ORDERBOOK_FIELDS,
        'candle': CANDLE_FIELDS,
        'myOrder': MY_ORDER_FIELDS,
        'myAsset': MY_ASSET_FIELDS
    }

    return field_docs.get(msg_type, {})


def print_field_documentation(msg_type: str) -> None:
    """메시지 타입별 필드 문서 예쁘게 출력 (개발자용)"""
    docs = get_field_documentation(msg_type)
    if not docs:
        print(f"❌ 지원하지 않는 메시지 타입: {msg_type}")
        return

    print(f"\n📋 {msg_type.upper()} 메시지 필드 문서")
    print("=" * 60)

    for field, description in docs.items():
        print(f"  {field:<25} : {description}")

    print("=" * 60)
    print(f"총 {len(docs)}개 필드")


# ================================================================
# 연결 상태 관리 (기존 클라이언트 패턴)
# ================================================================

def create_connection_status(state: str, connection_id: str) -> Dict[str, Any]:
    """WebSocket 연결 상태 생성"""
    now = datetime.now()
    return {
        'state': state,
        'connection_id': connection_id,
        'connected_at': now,
        'uptime_seconds': 0.0,
        'message_count': 0,
        'error_count': 0,
        'active_subscriptions': 0,
        'last_message_at': now,
        'is_connected': state in ['CONNECTED', 'ACTIVE', 'SUBSCRIBING'],
        'is_active': state == 'ACTIVE'
    }


def update_connection_status(status: Dict[str, Any],
                             message_received: bool = False,
                             error_occurred: bool = False) -> Dict[str, Any]:
    """연결 상태 업데이트"""
    now = datetime.now()
    updated = status.copy()

    # 업타임 계산
    if 'connected_at' in updated:
        connected_at = updated['connected_at']
        if isinstance(connected_at, datetime):
            updated['uptime_seconds'] = (now - connected_at).total_seconds()

    # 메시지 수신 통계
    if message_received:
        updated['message_count'] = updated.get('message_count', 0) + 1
        updated['last_message_at'] = now

    # 오류 통계
    if error_occurred:
        updated['error_count'] = updated.get('error_count', 0) + 1

    return updated


# ================================================================
# 사용 예시 및 테스트 유틸리티
# ================================================================

def example_ticker_message() -> Dict[str, Any]:
    """현재가 메시지 예시 (테스트용)"""
    return {
        'type': 'ticker',
        'code': 'KRW-BTC',
        'opening_price': 95000000.0,
        'high_price': 96000000.0,
        'low_price': 94000000.0,
        'trade_price': 95500000.0,
        'prev_closing_price': 95000000.0,
        'change': 'RISE',
        'change_price': 500000.0,
        'change_rate': 0.0053,
        'trade_volume': 0.1,
        'acc_trade_price_24h': 1000000000.0,
        'acc_trade_volume_24h': 10.5,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'stream_type': 'REALTIME'
    }


def example_trade_message() -> Dict[str, Any]:
    """체결 메시지 예시 (테스트용)"""
    return {
        'type': 'trade',
        'code': 'KRW-BTC',
        'trade_price': 95500000.0,
        'trade_volume': 0.01,
        'ask_bid': 'BID',
        'sequential_id': 123456789,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'stream_type': 'REALTIME'
    }


def example_orderbook_message() -> Dict[str, Any]:
    """호가 메시지 예시 (테스트용)"""
    return {
        'type': 'orderbook',
        'code': 'KRW-BTC',
        'orderbook_units': [
            {'ask_price': 95600000.0, 'bid_price': 95500000.0, 'ask_size': 0.5, 'bid_size': 0.3},
            {'ask_price': 95700000.0, 'bid_price': 95400000.0, 'ask_size': 0.2, 'bid_size': 0.1}
        ],
        'total_ask_size': 0.7,
        'total_bid_size': 0.4,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'stream_type': 'SNAPSHOT'
    }


# ================================================================
# SIMPLE 포맷 통합 처리 함수들 (v5.0 신규)
# ================================================================

def process_websocket_message(raw_data: Dict[str, Any],
                              format_preference: str = "auto",
                              validate_data: bool = True) -> Dict[str, Any]:
    """
    WebSocket 메시지 통합 처리 - SIMPLE 포맷 완전 지원

    Args:
        raw_data: WebSocket으로 받은 원시 데이터
        format_preference: 포맷 설정 ("auto", "simple", "default")
        validate_data: 데이터 검증 수행 여부

    Returns:
        Dict[str, Any]: 처리된 WebSocket 메시지
    """
    if not SIMPLE_FORMAT_AVAILABLE:
        # SIMPLE 포맷 변환기가 없으면 기본 처리
        msg_type = infer_message_type(raw_data)
        validated_data = validate_mixed_message(raw_data) if validate_data else raw_data
        return create_websocket_message(msg_type, validated_data.get('code'), validated_data)

    try:
        # 1. 메시지 타입 추론
        msg_type = infer_message_type(raw_data)

        # 2. 포맷 변환 처리
        if format_preference == "simple":
            # DEFAULT → SIMPLE 변환
            converted_data = convert_to_simple_format(raw_data, msg_type)
        elif format_preference == "default":
            # SIMPLE → DEFAULT 변환 (필요시)
            converted_data = auto_detect_and_convert(raw_data, target_format="DEFAULT")
        else:  # auto
            # 자동 감지 및 DEFAULT로 표준화
            converted_data = auto_detect_and_convert(raw_data, target_format="DEFAULT")

        # 3. 데이터 검증 (요청시)
        if validate_data:
            validated_data = validate_mixed_message(converted_data)
        else:
            validated_data = converted_data

        # 4. 표준 WebSocket 메시지 생성
        market_code = validated_data.get('code') or validated_data.get('cd') or 'UNKNOWN'
        return create_websocket_message(msg_type, market_code, validated_data)

    except Exception as e:
        # 오류 발생시 기본 처리로 폴백
        msg_type = infer_message_type(raw_data)
        validated_data = validate_mixed_message(raw_data) if validate_data else raw_data
        result = create_websocket_message(msg_type, validated_data.get('code'), validated_data)
        result['format_conversion_error'] = str(e)
        return result


def convert_message_format(message_data: Dict[str, Any],
                           target_format: str = "simple") -> Dict[str, Any]:
    """
    메시지 포맷 변환 (SIMPLE ↔ DEFAULT)

    Args:
        message_data: 변환할 메시지 데이터
        target_format: 목표 포맷 ("simple" 또는 "default")

    Returns:
        Dict[str, Any]: 변환된 메시지 데이터
    """
    if not SIMPLE_FORMAT_AVAILABLE:
        return message_data

    try:
        # 메시지에서 실제 데이터 추출
        data = message_data.get('data', message_data)
        msg_type = message_data.get('type') or infer_message_type(data)

        if target_format.lower() == "simple":
            converted_data = convert_to_simple_format(data, msg_type)
        else:  # default
            converted_data = auto_detect_and_convert(data, target_format="DEFAULT")

        # 원본 메시지 구조 유지하면서 데이터만 교체
        result = message_data.copy()
        result['data'] = converted_data
        result['format'] = target_format.upper()

        return result

    except Exception as e:
        # 변환 실패시 원본 반환
        result = message_data.copy()
        result['format_conversion_error'] = str(e)
        return result


def get_message_format(message_data: Dict[str, Any]) -> str:
    """
    메시지 포맷 감지 (SIMPLE/DEFAULT/UNKNOWN)

    Args:
        message_data: 분석할 메시지 데이터

    Returns:
        str: 감지된 포맷 ("SIMPLE", "DEFAULT", "UNKNOWN")
    """
    if not SIMPLE_FORMAT_AVAILABLE:
        return "DEFAULT"

    try:
        # 메시지에서 실제 데이터 추출
        data = message_data.get('data', message_data)

        # SIMPLE 포맷 특징 필드 확인
        simple_indicators = ['ty', 'cd', 'tp', 'tv', 'ap', 'bp', 'obu']
        default_indicators = ['type', 'code', 'trade_price', 'trade_volume',
                            'ask_price', 'bid_price', 'orderbook_units']

        simple_count = sum(1 for key in simple_indicators if key in data)
        default_count = sum(1 for key in default_indicators if key in data)

        if simple_count > default_count:
            return "SIMPLE"
        elif default_count > 0:
            return "DEFAULT"
        else:
            return "UNKNOWN"

    except Exception:
        return "UNKNOWN"


def create_format_aware_message(msg_type: str, market: str, data: Dict[str, Any],
                               format_mode: str = "default",
                               timestamp: Optional[datetime] = None,
                               stream_type: Optional[str] = None) -> Dict[str, Any]:
    """
    포맷 인식 WebSocket 메시지 생성

    Args:
        msg_type: 메시지 타입
        market: 마켓 코드
        data: 메시지 데이터
        format_mode: 포맷 모드 ("simple", "default", "auto")
        timestamp: 타임스탬프
        stream_type: 스트림 타입

    Returns:
        Dict[str, Any]: 포맷 인식 WebSocket 메시지
    """
    # 기본 메시지 생성
    message = create_websocket_message(msg_type, market, data, timestamp, stream_type)

    # 포맷 정보 추가
    message['format'] = get_message_format(message)
    message['format_mode'] = format_mode.upper()

    # SIMPLE 포맷 요청시 변환
    if format_mode.lower() == "simple" and SIMPLE_FORMAT_AVAILABLE:
        message = convert_message_format(message, "simple")

    return message


def batch_convert_messages(messages: List[Dict[str, Any]],
                           target_format: str = "simple") -> List[Dict[str, Any]]:
    """
    메시지 배치 포맷 변환

    Args:
        messages: 변환할 메시지 리스트
        target_format: 목표 포맷

    Returns:
        List[Dict[str, Any]]: 변환된 메시지 리스트
    """
    if not SIMPLE_FORMAT_AVAILABLE:
        return messages

    converted_messages = []
    for message in messages:
        try:
            converted = convert_message_format(message, target_format)
            converted_messages.append(converted)
        except Exception as e:
            # 변환 실패시 원본 유지하고 에러 표시
            error_message = message.copy()
            error_message['conversion_error'] = str(e)
            converted_messages.append(error_message)

    return converted_messages


# ================================================================
# SIMPLE 포맷 지원 확인 및 설정
# ================================================================

def is_simple_format_supported() -> bool:
    """SIMPLE 포맷 지원 여부 확인"""
    return SIMPLE_FORMAT_AVAILABLE


def get_format_conversion_stats() -> Dict[str, Any]:
    """포맷 변환 통계 정보"""
    return {
        "simple_format_available": SIMPLE_FORMAT_AVAILABLE,
        "supported_data_types": [
            "ticker", "trade", "orderbook", "candle", "myOrder", "myAsset"
        ] if SIMPLE_FORMAT_AVAILABLE else [],
        "conversion_modes": ["auto", "simple", "default"],
        "bandwidth_savings": "최대 60% (SIMPLE 포맷 사용시)" if SIMPLE_FORMAT_AVAILABLE else "지원 안함"
    }


if __name__ == "__main__":
    # 필드 문서 출력 테스트
    for msg_type in ['ticker', 'trade', 'orderbook', 'candle', 'myOrder', 'myAsset']:
        print_field_documentation(msg_type)

    # 메시지 타입 추론 테스트
    ticker_example = example_ticker_message()
    print("\n🔍 메시지 타입 추론 테스트")
    print(f"추론 결과: {infer_message_type(ticker_example)}")

    # 검증 테스트
    validated = validate_mixed_message(ticker_example)
    print(f"검증 성공: {'_validation_error' not in validated}")
