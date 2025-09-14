"""
업비트 REST API to WebSocket 형식 변환기

REST API 응답을 WebSocket models.py 형식으로 변환하여
완전한 API 통일성을 제공합니다.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


def convert_rest_ticker_to_websocket(rest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    REST API 현재가 응답을 WebSocket 형식으로 변환

    Args:
        rest_data: REST API /ticker 응답 데이터

    Returns:
        WebSocket 형식의 현재가 데이터
    """
    converted = {
        # 기본 식별자 (REST: market → WebSocket: code)
        'type': 'ticker',
        'code': rest_data.get('market', 'UNKNOWN'),

        # 가격 정보 (동일)
        'opening_price': rest_data.get('opening_price'),
        'high_price': rest_data.get('high_price'),
        'low_price': rest_data.get('low_price'),
        'trade_price': rest_data.get('trade_price'),
        'prev_closing_price': rest_data.get('prev_closing_price'),

        # 변동 정보 (동일)
        'change': rest_data.get('change'),
        'change_price': rest_data.get('change_price'),
        'change_rate': rest_data.get('change_rate'),
        'signed_change_price': rest_data.get('signed_change_price'),
        'signed_change_rate': rest_data.get('signed_change_rate'),

        # 거래량 정보 (동일)
        'trade_volume': rest_data.get('trade_volume'),
        'acc_trade_price': rest_data.get('acc_trade_price'),
        'acc_trade_volume': rest_data.get('acc_trade_volume'),
        'acc_trade_price_24h': rest_data.get('acc_trade_price_24h'),
        'acc_trade_volume_24h': rest_data.get('acc_trade_volume_24h'),

        # 52주 정보 (동일)
        'highest_52_week_price': rest_data.get('highest_52_week_price'),
        'highest_52_week_date': rest_data.get('highest_52_week_date'),
        'lowest_52_week_price': rest_data.get('lowest_52_week_price'),
        'lowest_52_week_date': rest_data.get('lowest_52_week_date'),

        # 시간 정보 (동일)
        'trade_date': rest_data.get('trade_date'),
        'trade_time': rest_data.get('trade_time'),
        'trade_date_kst': rest_data.get('trade_date_kst'),  # REST API 전용
        'trade_time_kst': rest_data.get('trade_time_kst'),  # REST API 전용
        'trade_timestamp': rest_data.get('trade_timestamp'),
        'timestamp': rest_data.get('timestamp'),

        # WebSocket 전용 필드 (기본값 설정)
        'stream_type': 'SNAPSHOT',  # REST API는 항상 스냅샷
        'ask_bid': None,  # REST API에서는 제공하지 않음
        'acc_ask_volume': None,
        'acc_bid_volume': None,

        # 메타데이터 (디버깅 및 추적용)
        '_source': 'rest_api',  # 데이터 원본: rest_api | websocket
        '_converted_at': datetime.now().isoformat()
    }

    # None 값 제거
    return {k: v for k, v in converted.items() if v is not None}


def convert_rest_orderbook_to_websocket(rest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    REST API 호가 응답을 WebSocket 형식으로 변환

    Args:
        rest_data: REST API /orderbook 응답 데이터

    Returns:
        WebSocket 형식의 호가 데이터
    """
    converted = {
        'type': 'orderbook',
        'code': rest_data.get('market', 'UNKNOWN'),
        'orderbook_units': rest_data.get('orderbook_units', []),
        'timestamp': rest_data.get('timestamp'),
        'stream_type': 'SNAPSHOT',  # REST API는 항상 스냅샷 형태
        '_source': 'rest_api',  # 데이터 원본: rest_api | websocket
        '_converted_at': datetime.now().isoformat()
    }

    # 총 잔량 계산 (WebSocket에는 있지만 REST에는 없음)
    orderbook_units = converted['orderbook_units']
    if orderbook_units:
        total_ask_size = sum(unit.get('ask_size', 0) for unit in orderbook_units)
        total_bid_size = sum(unit.get('bid_size', 0) for unit in orderbook_units)
        converted['total_ask_size'] = total_ask_size
        converted['total_bid_size'] = total_bid_size
        converted['level'] = len(orderbook_units)

    return {k: v for k, v in converted.items() if v is not None}


def convert_rest_candle_to_websocket(rest_data: Dict[str, Any],
                                     interval: str = '1m') -> Dict[str, Any]:
    """
    REST API 캔들 응답을 WebSocket 형식으로 변환

    역방향 변환 정보:
    - WebSocket → REST: 'code' → 'market', type에서 interval 추출
    - 시간 필드: 동일 (candle_date_time_utc/kst)
    - REST 전용 필드: unit (분 캔들), prev_closing_price, change_price, change_rate (일 캔들)
    - WebSocket 전용: stream_type

    Args:
        rest_data: REST API 캔들 응답 데이터 (초/분/일 캔들)
        interval: 캔들 간격 (1s, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 240m, 1d)

    Returns:
        WebSocket 형식의 캔들 데이터
    """
    # 간격을 WebSocket 타입으로 변환
    interval_map = {
        # WebSocket 지원 간격 (초/분)
        '1s': 'candle.1s',
        '1m': 'candle.1m', '3m': 'candle.3m', '5m': 'candle.5m',
        '10m': 'candle.10m', '15m': 'candle.15m', '30m': 'candle.30m',
        '60m': 'candle.60m', '240m': 'candle.240m',
        # WebSocket 미지원 (REST 전용) - 호환성을 위한 매핑
        '1d': 'candle.1d', '1w': 'candle.1w', '1M': 'candle.1M', '1y': 'candle.1y'
    }

    converted = {
        'type': interval_map.get(interval, f'candle.{interval}'),
        'code': rest_data.get('market', 'UNKNOWN'),

        # OHLC 데이터 (완전 호환)
        'opening_price': rest_data.get('opening_price'),
        'high_price': rest_data.get('high_price'),
        'low_price': rest_data.get('low_price'),
        'trade_price': rest_data.get('trade_price'),

        # 거래량 정보 (완전 호환)
        'candle_acc_trade_price': rest_data.get('candle_acc_trade_price'),
        'candle_acc_trade_volume': rest_data.get('candle_acc_trade_volume'),

        # 시간 정보 (완전 호환)
        'candle_date_time_utc': rest_data.get('candle_date_time_utc'),
        'candle_date_time_kst': rest_data.get('candle_date_time_kst'),
        'timestamp': rest_data.get('timestamp'),

        # WebSocket 전용 메타데이터
        'stream_type': 'SNAPSHOT',  # REST API는 항상 스냅샷
        '_source': 'rest_api',  # 데이터 원본: rest_api | websocket
        '_converted_at': datetime.now().isoformat(),
        '_conversion_info': {
            'original_interval': interval,
            'websocket_supported': interval in ['1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m'],
            'rest_only_fields': []
        }
    }

    # REST 전용 필드 처리 (역방향 변환 정보 보존)
    rest_only_fields = []

    # 분 캔들 전용: unit 필드
    if 'unit' in rest_data:
        converted['_rest_only_unit'] = rest_data.get('unit')
        rest_only_fields.append('unit')

    # 일/주/월/연 캔들 전용: 변동 정보
    day_plus_fields = ['prev_closing_price', 'change_price', 'change_rate', 'converted_trade_price']
    for field in day_plus_fields:
        if field in rest_data:
            converted[f'_rest_only_{field}'] = rest_data.get(field)
            rest_only_fields.append(field)

    # 변환 정보 업데이트
    converted['_conversion_info']['rest_only_fields'] = rest_only_fields

    # WebSocket 미지원 간격 표시
    if interval in ['1d', '1w', '1M', '1y']:
        converted['_conversion_info']['websocket_supported'] = False
        converted['_conversion_info']['note'] = f'WebSocket does not support {interval} interval'

    return {k: v for k, v in converted.items() if v is not None}


def convert_rest_trades_to_websocket(rest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    REST API 체결 응답을 WebSocket 형식으로 변환

    Args:
        rest_data: REST API 체결 응답 데이터

    Returns:
        WebSocket 형식의 체결 데이터
    """
    converted = {
        'type': 'trade',
        'code': rest_data.get('market', 'UNKNOWN'),

        # 체결 정보 (동일)
        'trade_price': rest_data.get('trade_price'),
        'trade_volume': rest_data.get('trade_volume'),
        'ask_bid': rest_data.get('ask_bid'),
        'sequential_id': rest_data.get('sequential_id'),

        # 가격 변동 정보
        'prev_closing_price': rest_data.get('prev_closing_price'),
        'change_price': rest_data.get('change_price'),
        'change': None,  # REST API에서는 RISE/FALL 정보 없음

        # 시간 정보 (필드명 변환)
        'trade_date': rest_data.get('trade_date_utc'),  # UTC → 일반 필드명
        'trade_time': rest_data.get('trade_time_utc'),  # UTC → 일반 필드명
        'trade_timestamp': rest_data.get('timestamp'),  # REST의 timestamp → trade_timestamp
        'timestamp': rest_data.get('timestamp'),

        # WebSocket 전용 필드 (REST에서는 제공 안됨)
        'best_ask_price': None,  # 최우선 매도 호가 (호가 API 별도 필요)
        'best_ask_size': None,   # 최우선 매도 잔량
        'best_bid_price': None,  # 최우선 매수 호가
        'best_bid_size': None,   # 최우선 매수 잔량

        # 스트림 메타데이터
        'stream_type': 'SNAPSHOT',  # REST API는 항상 스냅샷
        '_source': 'rest_api',  # 데이터 원본: rest_api | websocket
        '_converted_at': datetime.now().isoformat(),
        '_missing_fields': ['change', 'best_ask_price', 'best_bid_price', 'best_ask_size', 'best_bid_size']
    }

    return {k: v for k, v in converted.items() if v is not None}


def convert_rest_market_to_websocket(rest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    REST API 마켓 목록을 WebSocket 호환 형식으로 변환

    Args:
        rest_data: REST API 마켓 데이터

    Returns:
        WebSocket 호환 형식의 마켓 데이터
    """
    converted = {
        'type': 'market',
        'code': rest_data.get('market', 'UNKNOWN'),
        'market': rest_data.get('market'),
        'korean_name': rest_data.get('korean_name'),
        'english_name': rest_data.get('english_name'),
        'market_event': rest_data.get('market_event'),
        'market_warning': rest_data.get('market_warning'),
        'stream_type': 'SNAPSHOT',
        '_source': 'rest_api',
        '_converted_at': datetime.now().isoformat()
    }

    return {k: v for k, v in converted.items() if v is not None}


def batch_convert_rest_to_websocket(rest_data_list: List[Dict[str, Any]],
                                    data_type: str,
                                    **kwargs) -> List[Dict[str, Any]]:
    """
    REST API 응답 배열을 WebSocket 형식으로 일괄 변환

    Args:
        rest_data_list: REST API 응답 배열
        data_type: 데이터 타입 (ticker, orderbook, candle, trade, market, order)
        **kwargs: 변환 함수별 추가 파라미터

    Returns:
        WebSocket 형식 데이터 배열
    """
    conversion_map = {
        'ticker': convert_rest_ticker_to_websocket,
        'orderbook': convert_rest_orderbook_to_websocket,
        'candle': convert_rest_candle_to_websocket,
        'trade': convert_rest_trades_to_websocket,
        'market': convert_rest_market_to_websocket,
        'order': convert_rest_order_to_websocket
    }

    converter = conversion_map.get(data_type)
    if not converter:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")

    converted_list = []
    for item in rest_data_list:
        try:
            if data_type == 'candle':
                converted = converter(item, **kwargs)
            else:
                converted = converter(item)
            converted_list.append(converted)
        except Exception as e:
            # 변환 실패 시 오류 정보 포함하여 추가
            error_item = {
                'type': f'{data_type}_error',
                'code': item.get('market', 'UNKNOWN'),
                'error': str(e),
                'original_data': item,
                '_source': 'rest_api_conversion_error',
                '_converted_at': datetime.now().isoformat()
            }
            converted_list.append(error_item)

    return converted_list


def convert_websocket_to_rest_candle(ws_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket 캔들 데이터를 REST API 형식으로 역변환

    Args:
        ws_data: WebSocket 캔들 데이터

    Returns:
        REST API 형식의 캔들 데이터
    """
    # WebSocket type에서 interval 추출 (메타데이터용)
    ws_type = ws_data.get('type', 'candle.1m')

    converted = {
        'market': ws_data.get('code', 'UNKNOWN'),

        # OHLC 데이터 (완전 호환)
        'opening_price': ws_data.get('opening_price'),
        'high_price': ws_data.get('high_price'),
        'low_price': ws_data.get('low_price'),
        'trade_price': ws_data.get('trade_price'),

        # 거래량 정보 (완전 호환)
        'candle_acc_trade_price': ws_data.get('candle_acc_trade_price'),
        'candle_acc_trade_volume': ws_data.get('candle_acc_trade_volume'),

        # 시간 정보 (완전 호환)
        'candle_date_time_utc': ws_data.get('candle_date_time_utc'),
        'candle_date_time_kst': ws_data.get('candle_date_time_kst'),
        'timestamp': ws_data.get('timestamp'),

        # 메타데이터
        '_source': 'websocket',
        '_converted_at': datetime.now().isoformat(),
        '_original_type': ws_type
    }

    # REST 전용 필드 복원 (변환 시 보존된 정보 활용)
    for key, value in ws_data.items():
        if key.startswith('_rest_only_'):
            original_field = key.replace('_rest_only_', '')
            converted[original_field] = value

    return {k: v for k, v in converted.items() if v is not None}


def convert_rest_order_to_websocket(rest_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    REST API 주문 응답을 WebSocket MyOrder 형식으로 변환

    지원하는 REST API 엔드포인트:
    - /v1/order (개별 주문 조회) - trades 배열 포함
    - /v1/orders/uuids (UUID 목록 조회) - trades 없음
    - /v1/orders/open (체결 대기 목록) - trades 없음
    - /v1/orders/closed (종료 주문 목록) - trades 없음

    필드 매핑 제한사항:
    - trade_uuid, trade_timestamp: /v1/order에서만 가능
    - avg_price: 모든 REST API에서 제공하지 않음 (WebSocket 전용)
    - executed_funds: /v1/orders/closed에서는 없음

    Args:
        rest_data: REST API 주문 응답 데이터

    Returns:
        WebSocket MyOrder 형식의 주문 데이터 (필드별 REST API 소스 주석 포함)
    """
    converted = {
        'type': 'myOrder',
        'code': rest_data.get('market', 'UNKNOWN'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 주문 기본 정보
        'uuid': rest_data.get('uuid'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'ask_bid': rest_data.get('side'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'order_type': rest_data.get('ord_type'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'state': rest_data.get('state'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'price': rest_data.get('price'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 수량 정보
        'volume': rest_data.get('volume'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'remaining_volume': rest_data.get('remaining_volume'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'executed_volume': rest_data.get('executed_volume'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 금액 정보
        'executed_funds': rest_data.get('executed_funds'),  # /order, /orders/uuids, /orders/open (closed에는 없음)

        # 수수료 정보
        'reserved_fee': rest_data.get('reserved_fee'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'remaining_fee': rest_data.get('remaining_fee'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'paid_fee': rest_data.get('paid_fee'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'locked': rest_data.get('locked'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 고급 주문 기능
        'time_in_force': rest_data.get('time_in_force'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'identifier': rest_data.get('identifier'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # SMP(자전거래 방지) 기능
        'smp_type': rest_data.get('smp_type'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'prevented_volume': rest_data.get('prevented_volume'),  # /order, /orders/uuids, /orders/open, /orders/closed
        'prevented_locked': rest_data.get('prevented_locked'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 체결 정보
        'trades_count': rest_data.get('trades_count'),  # /order, /orders/uuids, /orders/open, /orders/closed

        # 시간 정보
        'order_timestamp': None,  # /order, /orders/uuids, /orders/open, /orders/closed (created_at 변환)
        'timestamp': None,  # 현재 시간으로 설정

        # WebSocket 전용 메타데이터
        'stream_type': 'SNAPSHOT',  # WebSocket 전용 (REST에서는 항상 SNAPSHOT)
        '_source': 'rest_api',  # 데이터 원본: rest_api | websocket
        '_converted_at': datetime.now().isoformat(),
        '_conversion_info': {
            'rest_only_fields': [],
            'websocket_only_fields': ['stream_type', 'trade_timestamp', 'trade_uuid', 'avg_price'],
            'field_mappings': {
                'market': 'code',
                'side': 'ask_bid',
                'ord_type': 'order_type',
                'created_at': 'order_timestamp'
            },
            'rest_api_sources': {
                'individual_order': '/v1/order',  # 개별 주문 조회 (trades 포함)
                'orders_by_uuids': '/v1/orders/uuids',  # UUID 목록으로 조회
                'open_orders': '/v1/orders/open',  # 체결 대기 주문 목록
                'closed_orders': '/v1/orders/closed',  # 종료 주문 목록
                'order_chance': '/v1/orders/chance'  # 주문 가능 정보 (별도 처리 필요)
            }
        }
    }

    # 시간 필드 변환 (ISO 문자열 → milliseconds)
    created_at = rest_data.get('created_at')
    if created_at:
        try:
            # ISO 문자열을 datetime으로 파싱 후 milliseconds로 변환
            # KST 타임존 제거 (+09:00)
            clean_time = re.sub(r'\+\d{2}:\d{2}$', '', created_at)
            dt_obj = datetime.fromisoformat(clean_time)
            converted['order_timestamp'] = int(dt_obj.timestamp() * 1000)
        except Exception:
            converted['order_timestamp'] = None

    # 현재 시간을 timestamp로 설정 (WebSocket과 동일)
    converted['timestamp'] = int(datetime.now().timestamp() * 1000)

    # REST 전용 필드 처리 (역방향 변환 정보 보존)
    rest_only_fields = []

    # executed_funds는 REST 전용
    if 'executed_funds' in rest_data:
        converted['_rest_only_executed_funds'] = rest_data.get('executed_funds')
        rest_only_fields.append('executed_funds')

    # trades 배열 처리 (WebSocket에서는 개별 메시지)
    trades = rest_data.get('trades', [])  # /order 전용 (목록 조회에는 없음)
    if trades:
        converted['_rest_only_trades'] = trades
        rest_only_fields.append('trades')

        # 최신 체결 정보를 주문 데이터에 포함 (WebSocket 스타일)
        if trades:
            latest_trade = trades[0]  # 가장 최근 체결
            converted['trade_uuid'] = latest_trade.get('uuid')  # /order의 trades[].uuid
            converted['avg_price'] = None  # REST에서는 제공하지 않음 (WebSocket 전용)

            # 체결 시간 (WebSocket에서는 trade_timestamp)
            trade_created_at = latest_trade.get('created_at')  # /order의 trades[].created_at
            if trade_created_at:
                try:
                    clean_time = re.sub(r'\+\d{2}:\d{2}$', '', trade_created_at)
                    trade_dt = datetime.fromisoformat(clean_time.replace('T', ' '))
                    converted['trade_timestamp'] = int(trade_dt.timestamp() * 1000)
                except Exception:
                    converted['trade_timestamp'] = None
    else:
        # 목록 조회 시에는 체결 정보 없음
        converted['trade_uuid'] = None  # /orders/uuids, /orders/open, /orders/closed에서는 없음
        converted['avg_price'] = None  # 모든 REST API에서 제공하지 않음
        converted['trade_timestamp'] = None  # /orders/uuids, /orders/open, /orders/closed에서는 없음

    # 변환 정보 업데이트
    converted['_conversion_info']['rest_only_fields'] = rest_only_fields

    # WebSocket 단축 필드명 추가 (선택적 호환성)
    converted['ab'] = converted['ask_bid']     # ask_bid
    converted['ot'] = converted['order_type']  # order_type
    converted['s'] = converted['state']        # state
    converted['p'] = converted['price']        # price
    converted['v'] = converted['volume']       # volume
    converted['rv'] = converted['remaining_volume']  # remaining_volume
    converted['ev'] = converted['executed_volume']   # executed_volume
    converted['tc'] = converted['trades_count']      # trades_count

    return {k: v for k, v in converted.items() if v is not None}


def convert_websocket_order_to_rest(ws_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    WebSocket MyOrder 데이터를 REST API 형식으로 역변환

    Args:
        ws_data: WebSocket MyOrder 데이터

    Returns:
        REST API 형식의 주문 데이터
    """
    converted = {
        'market': ws_data.get('code', 'UNKNOWN'),
        'uuid': ws_data.get('uuid'),
        'side': ws_data.get('ask_bid'),
        'ord_type': ws_data.get('order_type'),
        'state': ws_data.get('state'),
        'price': ws_data.get('price'),
        'volume': ws_data.get('volume'),
        'remaining_volume': ws_data.get('remaining_volume'),
        'executed_volume': ws_data.get('executed_volume'),
        'reserved_fee': ws_data.get('reserved_fee'),
        'remaining_fee': ws_data.get('remaining_fee'),
        'paid_fee': ws_data.get('paid_fee'),
        'locked': ws_data.get('locked'),
        'time_in_force': ws_data.get('time_in_force'),
        'identifier': ws_data.get('identifier'),
        'smp_type': ws_data.get('smp_type'),
        'prevented_volume': ws_data.get('prevented_volume'),
        'prevented_locked': ws_data.get('prevented_locked'),
        'trades_count': ws_data.get('trades_count'),
        '_source': 'websocket',
        '_converted_at': datetime.now().isoformat(),
        '_original_type': ws_data.get('type', 'myOrder')
    }

    # 시간 필드 변환 (milliseconds → ISO 문자열)
    order_timestamp = ws_data.get('order_timestamp')
    if order_timestamp:
        try:
            dt_obj = datetime.fromtimestamp(order_timestamp / 1000)
            converted['created_at'] = dt_obj.strftime('%Y-%m-%dT%H:%M:%S+09:00')
        except Exception:
            converted['created_at'] = None

    # REST 전용 필드 복원 (변환 시 보존된 정보 활용)
    for key, value in ws_data.items():
        if key.startswith('_rest_only_'):
            original_field = key.replace('_rest_only_', '')
            converted[original_field] = value

    return {k: v for k, v in converted.items() if v is not None}


def create_unified_response(data: Any, source: str, data_type: str) -> Dict[str, Any]:
    """
    통합된 API 응답 생성

    Args:
        data: 실제 데이터 (WebSocket 형식으로 변환됨)
        source: 데이터 소스 ('rest_api' 또는 'websocket')
        data_type: 데이터 타입

    Returns:
        통합된 응답 형식
    """
    return {
        'data': data,
        'metadata': {
            'source': source,
            'data_type': data_type,
            'timestamp': datetime.now().isoformat(),
            'format': 'websocket_compatible',
            'count': len(data) if isinstance(data, list) else 1
        },
        'success': True
    }


def convert_rest_asset_to_websocket(rest_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    REST API 자산 응답을 WebSocket 형식으로 변환

    Args:
        rest_data: REST API /v1/accounts 응답 데이터 (배열)

    Returns:
        WebSocket MyAsset 형식의 자산 데이터
    """
    # REST API에서 제공하지 않는 WebSocket 전용 필드들
    asset_uuid = None  # N/A (WebSocket only)
    asset_timestamp = int(datetime.now().timestamp() * 1000)  # N/A (WebSocket only)
    timestamp = int(datetime.now().timestamp() * 1000)

    # REST API 자산 목록을 WebSocket assets 배열로 변환
    assets = []
    for account in rest_data:
        asset_item = {
            'currency': account.get('currency'),  # /v1/accounts
            'balance': account.get('balance'),  # /v1/accounts
            'locked': account.get('locked'),  # /v1/accounts

            # REST API 전용 필드들 (WebSocket에서는 제공하지 않음)
            '_rest_only_avg_buy_price': account.get('avg_buy_price'),  # /v1/accounts
            '_rest_only_avg_buy_price_modified': account.get('avg_buy_price_modified'),  # /v1/accounts
            '_rest_only_unit_currency': account.get('unit_currency')  # /v1/accounts
        }

        # None 값 제거 (WebSocket과 일관성 유지)
        asset_item = {k: v for k, v in asset_item.items() if v is not None}
        assets.append(asset_item)

    converted = {
        'type': 'myAsset',  # N/A (WebSocket only)
        'asset_uuid': asset_uuid,  # N/A (WebSocket only)
        'assets': assets,  # /v1/accounts (currency, balance, locked)
        'asset_timestamp': asset_timestamp,  # N/A (WebSocket only)
        'timestamp': timestamp,  # N/A (WebSocket only)
        'stream_type': 'SNAPSHOT',  # N/A (WebSocket only)

        # 메타데이터 및 변환 정보
        '_source': 'rest_api',
        '_converted_at': datetime.now().isoformat(),
        '_conversion_info': {
            'rest_only_fields': ['avg_buy_price', 'avg_buy_price_modified', 'unit_currency'],
            'websocket_only_fields': ['type', 'asset_uuid', 'asset_timestamp', 'timestamp', 'stream_type'],
            'field_mappings': {
                'accounts': 'assets'  # REST는 accounts 배열, WebSocket은 assets 배열
            },
            'rest_api_sources': {
                'currency': '/v1/accounts',
                'balance': '/v1/accounts',
                'locked': '/v1/accounts',
                'type': 'N/A (WebSocket only)',
                'asset_uuid': 'N/A (WebSocket only)',
                'asset_timestamp': 'N/A (WebSocket only)',
                'timestamp': 'N/A (WebSocket only)',
                'stream_type': 'N/A (WebSocket only)'
            }
        }
    }

    return converted


def convert_websocket_asset_to_rest(websocket_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    WebSocket MyAsset 데이터를 REST API 형식으로 역변환

    Args:
        websocket_data: WebSocket MyAsset 형식 데이터

    Returns:
        REST API /v1/accounts 형식의 자산 데이터 (배열)
    """
    assets = websocket_data.get('assets', [])

    rest_accounts = []
    for asset in assets:
        account = {
            'currency': asset.get('currency'),
            'balance': asset.get('balance'),
            'locked': asset.get('locked'),

            # REST 전용 필드들 (변환 시 복원)
            'avg_buy_price': asset.get('_rest_only_avg_buy_price', '0'),
            'avg_buy_price_modified': asset.get('_rest_only_avg_buy_price_modified', False),
            'unit_currency': asset.get('_rest_only_unit_currency', 'KRW')
        }

        # None 값을 적절한 기본값으로 대체
        if account['balance'] is None:
            account['balance'] = '0'
        if account['locked'] is None:
            account['locked'] = '0'

        rest_accounts.append(account)

    return rest_accounts
