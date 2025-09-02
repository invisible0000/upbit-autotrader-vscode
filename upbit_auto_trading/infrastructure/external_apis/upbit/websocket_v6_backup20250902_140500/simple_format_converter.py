"""
업비트 WebSocket v5.0 - SIMPLE 포맷 변환기

🎯 특징:
- 업비트 공식 SIMPLE 포맷 지원 (압축 전송용)
- 양방향 변환: DEFAULT ↔ SIMPLE
- 자동 포맷 감지 및 검증
- 모든 WebSocket 데이터 타입 지원 (Ticker, Trade, Orderbook, Candle, MyOrder)
"""

from typing import Dict, Any

# ================================================================
# TICKER SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

TICKER_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    # 💰 가격 정보 (OHLC + 현재가)
    'opening_price': 'op', 'high_price': 'hp', 'low_price': 'lp', 'trade_price': 'tp', 'prev_closing_price': 'pcp',
    # 📈 변화량 정보
    'change': 'c', 'change_price': 'cp', 'signed_change_price': 'scp', 'change_rate': 'cr', 'signed_change_rate': 'scr',
    # 📊 거래량 정보
    'trade_volume': 'tv', 'acc_trade_volume': 'atv', 'acc_trade_volume_24h': 'atv24h',
    'acc_trade_price': 'atp', 'acc_trade_price_24h': 'atp24h',
    # ⏰ 거래 시각 정보
    'trade_date': 'tdt', 'trade_time': 'ttm', 'trade_timestamp': 'ttms',
    # 🎯 매수/매도 구분
    'ask_bid': 'ab',
    # 📈 누적량 분석
    'acc_ask_volume': 'aav', 'acc_bid_volume': 'abv',
    # 🏆 52주 최고/최저
    'highest_52_week_price': 'h52wp', 'highest_52_week_date': 'h52wdt',
    'lowest_52_week_price': 'l52wp', 'lowest_52_week_date': 'l52wdt',
    # 🎯 시장 상태 정보
    'market_state': 'ms', 'market_state_for_ios': 'msfi', 'is_trading_suspended': 'its',
    'delisting_date': 'dd', 'market_warning': 'mw', 'trade_status': 'ts',
}

TICKER_SIMPLE_REVERSE_MAPPING = {v: k for k, v in TICKER_SIMPLE_MAPPING.items()}

# ================================================================
# TRADE SIMPLE 포맷 매핑
# ================================================================

TRADE_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    # 💰 체결 정보
    'trade_price': 'tp', 'trade_volume': 'tv', 'ask_bid': 'ab', 'prev_closing_price': 'pcp',
    # 📈 변화 정보
    'change': 'c', 'change_price': 'cp',
    # ⏰ 체결 시각 정보
    'trade_date': 'td', 'trade_time': 'ttm', 'trade_timestamp': 'ttms',
    # 🔢 체결 고유번호
    'sequential_id': 'sid',
    # 🏆 최우선 호가 정보
    'best_ask_price': 'bap', 'best_ask_size': 'bas', 'best_bid_price': 'bbp', 'best_bid_size': 'bbs',
}

TRADE_SIMPLE_REVERSE_MAPPING = {v: k for k, v in TRADE_SIMPLE_MAPPING.items()}

# ================================================================
# ORDERBOOK SIMPLE 포맷 매핑
# ================================================================

ORDERBOOK_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    # 📊 총 잔량 정보
    'total_ask_size': 'tas', 'total_bid_size': 'tbs',
    # 🏢 호가 데이터 배열
    'orderbook_units': 'obu',
    # 🔢 호가 모아보기 설정
    'level': 'lv',
}

ORDERBOOK_UNITS_SIMPLE_MAPPING = {
    'ask_price': 'ap', 'bid_price': 'bp', 'ask_size': 'as', 'bid_size': 'bs',
}

ORDERBOOK_SIMPLE_REVERSE_MAPPING = {v: k for k, v in ORDERBOOK_SIMPLE_MAPPING.items()}
ORDERBOOK_UNITS_SIMPLE_REVERSE_MAPPING = {v: k for k, v in ORDERBOOK_UNITS_SIMPLE_MAPPING.items()}

# ================================================================
# CANDLE SIMPLE 포맷 매핑
# ================================================================

CANDLE_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'code': 'cd', 'timestamp': 'tms', 'stream_type': 'st',
    # ⏰ 캔들 시간 정보
    'candle_date_time_utc': 'cdttmu', 'candle_date_time_kst': 'cdttmk',
    # 💰 OHLC 가격 정보
    'opening_price': 'op', 'high_price': 'hp', 'low_price': 'lp', 'trade_price': 'tp', 'prev_closing_price': 'pcp',
    # 📊 거래량 정보
    'candle_acc_trade_volume': 'catv', 'candle_acc_trade_price': 'catp',
    # 📈 변화 정보
    'change': 'c', 'change_price': 'cp', 'change_rate': 'cr', 'signed_change_price': 'scp', 'signed_change_rate': 'scr',
    # 🎯 캔들 단위별 고유 정보
    'unit': 'u',
}

CANDLE_SIMPLE_REVERSE_MAPPING = {v: k for k, v in CANDLE_SIMPLE_MAPPING.items()}

# ================================================================
# MYORDER SIMPLE 포맷 매핑
# ================================================================

MYORDER_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'code': 'cd', 'uuid': 'uid', 'timestamp': 'tms', 'stream_type': 'st',
    # 💰 주문 기본 정보
    'ask_bid': 'ab', 'order_type': 'ot', 'state': 's', 'trade_uuid': 'tuid',
    # 💲 가격 정보
    'price': 'p', 'avg_price': 'ap', 'volume': 'v', 'remaining_volume': 'rv', 'executed_volume': 'ev',
    # 📊 체결 및 수수료 정보
    'trades_count': 'tc', 'reserved_fee': 'rsf', 'remaining_fee': 'rmf', 'paid_fee': 'pf',
    'locked': 'l', 'executed_funds': 'ef', 'trade_fee': 'tf',
    # 🎯 주문 조건 및 특성
    'time_in_force': 'tif', 'is_maker': 'im', 'identifier': 'id',
    # 🔒 자전거래 체결 방지 (SMP) 관련
    'smp_type': 'smpt', 'prevented_volume': 'pv', 'prevented_locked': 'pl',
    # ⏰ 시간 정보
    'trade_timestamp': 'ttms', 'order_timestamp': 'otms',
}

MYORDER_SIMPLE_REVERSE_MAPPING = {v: k for k, v in MYORDER_SIMPLE_MAPPING.items()}

# ================================================================
# MYASSET SIMPLE 포맷 매핑
# ================================================================

MYASSET_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty', 'asset_uuid': 'astuid', 'timestamp': 'tms', 'stream_type': 'st',
    # 💰 자산 정보
    'assets': 'ast', 'asset_timestamp': 'asttms',
}

# 📋 Assets 내부 필드 SIMPLE 매핑 (각 자산 아이템의 필드들)
MYASSET_ASSETS_SIMPLE_MAPPING = {
    'currency': 'cu', 'balance': 'b', 'locked': 'l',
}

MYASSET_SIMPLE_REVERSE_MAPPING = {v: k for k, v in MYASSET_SIMPLE_MAPPING.items()}
MYASSET_ASSETS_SIMPLE_REVERSE_MAPPING = {v: k for k, v in MYASSET_ASSETS_SIMPLE_MAPPING.items()}

# ================================================================
# SIMPLE 포맷 변환 함수들
# ================================================================


def convert_ticker_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ticker SIMPLE → DEFAULT 변환"""
    return {TICKER_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_ticker_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ticker DEFAULT → SIMPLE 변환"""
    return {TICKER_SIMPLE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_trade_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade SIMPLE → DEFAULT 변환"""
    return {TRADE_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_trade_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade DEFAULT → SIMPLE 변환"""
    return {TRADE_SIMPLE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_orderbook_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Orderbook SIMPLE → DEFAULT 변환"""
    converted = {}
    for simple_key, value in data.items():
        default_key = ORDERBOOK_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        if simple_key == 'obu' and isinstance(value, list):
            converted_units = []
            for unit in value:
                if isinstance(unit, dict):
                    converted_unit = {ORDERBOOK_UNITS_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in unit.items()}
                    converted_units.append(converted_unit)
                else:
                    converted_units.append(unit)
            converted[default_key] = converted_units
        else:
            converted[default_key] = value
    return converted


def convert_orderbook_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Orderbook DEFAULT → SIMPLE 변환"""
    converted = {}
    for default_key, value in data.items():
        simple_key = ORDERBOOK_SIMPLE_MAPPING.get(default_key, default_key)
        if default_key == 'orderbook_units' and isinstance(value, list):
            converted_units = []
            for unit in value:
                if isinstance(unit, dict):
                    converted_unit = {ORDERBOOK_UNITS_SIMPLE_MAPPING.get(k, k): v for k, v in unit.items()}
                    converted_units.append(converted_unit)
                else:
                    converted_units.append(unit)
            converted[simple_key] = converted_units
        else:
            converted[simple_key] = value
    return converted


def convert_candle_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle SIMPLE → DEFAULT 변환"""
    return {CANDLE_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_candle_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle DEFAULT → SIMPLE 변환"""
    return {CANDLE_SIMPLE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_myorder_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder SIMPLE → DEFAULT 변환"""
    return {MYORDER_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_myorder_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder DEFAULT → SIMPLE 변환"""
    return {MYORDER_SIMPLE_MAPPING.get(k, k): v for k, v in data.items()}


def convert_myasset_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyAsset SIMPLE → DEFAULT 변환"""
    converted = {}
    for simple_key, value in data.items():
        default_key = MYASSET_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        if simple_key == 'ast' and isinstance(value, list):
            converted_assets = []
            for asset in value:
                if isinstance(asset, dict):
                    converted_asset = {MYASSET_ASSETS_SIMPLE_REVERSE_MAPPING.get(k, k): v for k, v in asset.items()}
                    converted_assets.append(converted_asset)
                else:
                    converted_assets.append(asset)
            converted[default_key] = converted_assets
        else:
            converted[default_key] = value
    return converted


def convert_myasset_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyAsset DEFAULT → SIMPLE 변환"""
    converted = {}
    for default_key, value in data.items():
        simple_key = MYASSET_SIMPLE_MAPPING.get(default_key, default_key)
        if default_key == 'assets' and isinstance(value, list):
            converted_assets = []
            for asset in value:
                if isinstance(asset, dict):
                    converted_asset = {MYASSET_ASSETS_SIMPLE_MAPPING.get(k, k): v for k, v in asset.items()}
                    converted_assets.append(converted_asset)
                else:
                    converted_assets.append(asset)
            converted[simple_key] = converted_assets
        else:
            converted[simple_key] = value
    return converted

# ================================================================
# 포맷 감지 함수들
# ================================================================


def detect_ticker_format(data: Dict[str, Any]) -> str:
    """Ticker 포맷 감지"""
    simple_indicators = ['ty', 'cd', 'tp', 'op', 'hp', 'lp']
    default_indicators = ['type', 'code', 'trade_price', 'opening_price']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def detect_trade_format(data: Dict[str, Any]) -> str:
    """Trade 포맷 감지"""
    simple_indicators = ['ty', 'cd', 'tp', 'tv', 'ab', 'sid']
    default_indicators = ['type', 'code', 'trade_price', 'trade_volume', 'ask_bid', 'sequential_id']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def detect_orderbook_format(data: Dict[str, Any]) -> str:
    """Orderbook 포맷 감지"""
    simple_indicators = ['ty', 'cd', 'tas', 'tbs', 'obu']
    default_indicators = ['type', 'code', 'total_ask_size', 'total_bid_size', 'orderbook_units']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def detect_candle_format(data: Dict[str, Any]) -> str:
    """Candle 포맷 감지"""
    simple_indicators = ['ty', 'cd', 'cdttmu', 'op', 'hp', 'lp', 'tp', 'catv']
    default_indicators = ['type', 'code', 'candle_date_time_utc', 'opening_price',
                          'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def detect_myorder_format(data: Dict[str, Any]) -> str:
    """MyOrder 포맷 감지"""
    simple_indicators = ['ty', 'cd', 'uid', 'ab', 'ot', 's', 'p', 'v']
    default_indicators = ['type', 'code', 'uuid', 'ask_bid', 'order_type', 'state', 'price', 'volume']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def detect_myasset_format(data: Dict[str, Any]) -> str:
    """MyAsset 포맷 감지"""
    simple_indicators = ['ty', 'astuid', 'ast', 'asttms']
    default_indicators = ['type', 'asset_uuid', 'assets', 'asset_timestamp']
    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)
    return "SIMPLE" if simple_count > default_count else "DEFAULT"

# ================================================================
# 검증 함수들
# ================================================================


def validate_ticker_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ticker SIMPLE 포맷 검증"""
    required_fields = ['cd', 'tp']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Ticker SIMPLE 필수 필드 누락: {field}")
    price_fields = ['op', 'hp', 'lp', 'tp', 'pcp']
    for field in price_fields:
        if field in data and data[field] is not None:
            if float(data[field]) <= 0:
                raise ValueError(f"Ticker SIMPLE 가격 필드는 양수여야 함: {field}={data[field]}")
    return data


def validate_trade_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade SIMPLE 포맷 검증"""
    required_fields = ['cd', 'tp', 'tv', 'ab', 'sid']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Trade SIMPLE 필수 필드 누락: {field}")
    if data['ab'] not in ['ASK', 'BID']:
        raise ValueError(f"Trade SIMPLE 매수/매도 구분 오류: {data['ab']}")
    if float(data['tp']) <= 0 or float(data['tv']) <= 0:
        raise ValueError("Trade SIMPLE 체결가/체결량은 양수여야 함")
    return data


def validate_orderbook_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Orderbook SIMPLE 포맷 검증"""
    required_fields = ['cd', 'obu']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Orderbook SIMPLE 필수 필드 누락: {field}")
    if not isinstance(data['obu'], list) or len(data['obu']) == 0:
        raise ValueError("Orderbook SIMPLE 호가 정보가 비어있음")
    for i, unit in enumerate(data['obu']):
        if not isinstance(unit, dict):
            raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 타입 오류")
        unit_required = ['ap', 'bp', 'as', 'bs']
        for field in unit_required:
            if field not in unit or unit[field] is None:
                raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 필수 필드 누락: {field}")
            if float(unit[field]) < 0:
                raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 필드는 음수 불가: {field}")
    return data


def validate_candle_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle SIMPLE 포맷 검증"""
    required_fields = ['cd', 'op', 'hp', 'lp', 'tp', 'catv', 'catp']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Candle SIMPLE 필수 필드 누락: {field}")
    # OHLC 검증
    op, hp, lp, tp = float(data['op']), float(data['hp']), float(data['lp']), float(data['tp'])
    if not (lp <= op <= hp and lp <= tp <= hp):
        raise ValueError(f"Candle SIMPLE OHLC 논리 오류: O={op}, H={hp}, L={lp}, C={tp}")
    # 거래량 검증
    if float(data['catv']) < 0 or float(data['catp']) < 0:
        raise ValueError("Candle SIMPLE 거래량 필드는 음수 불가")
    return data


def validate_myorder_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder SIMPLE 포맷 검증"""
    required_fields = ['cd', 'uid', 'ab', 'ot', 's']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"MyOrder SIMPLE 필수 필드 누락: {field}")
    if data['ab'] not in ['ASK', 'BID']:
        raise ValueError(f"MyOrder SIMPLE 매수/매도 구분 오류: {data['ab']}")
    valid_order_types = ['limit', 'price', 'market', 'best']
    if data['ot'] not in valid_order_types:
        raise ValueError(f"MyOrder SIMPLE 주문 타입 오류: {data['ot']}")
    valid_states = ['wait', 'watch', 'trade', 'done', 'cancel', 'prevented']
    if data['s'] not in valid_states:
        raise ValueError(f"MyOrder SIMPLE 주문 상태 오류: {data['s']}")
    return data


def validate_myasset_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyAsset SIMPLE 포맷 검증"""
    required_fields = ['astuid', 'ast']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"MyAsset SIMPLE 필수 필드 누락: {field}")
    if not isinstance(data['ast'], list) or len(data['ast']) == 0:
        raise ValueError("MyAsset SIMPLE 자산 정보가 비어있음")
    for i, asset in enumerate(data['ast']):
        if not isinstance(asset, dict):
            raise ValueError(f"MyAsset SIMPLE 자산 아이템 {i} 타입 오류")
        asset_required = ['cu', 'b', 'l']
        for field in asset_required:
            if field not in asset or asset[field] is None:
                raise ValueError(f"MyAsset SIMPLE 자산 {i} 필수 필드 누락: {field}")
            if field in ['b', 'l'] and float(asset[field]) < 0:
                raise ValueError(f"MyAsset SIMPLE 자산 {i} 수량 필드는 음수 불가: {field}")
    return data

# ================================================================
# 통합 변환기
# ================================================================


def convert_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """자동 타입 감지하여 SIMPLE → DEFAULT 변환"""
    return auto_detect_and_convert(data)


def convert_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """자동 타입 감지하여 DEFAULT → SIMPLE 변환"""
    return auto_detect_and_convert(data)


def convert_to_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 적절한 SIMPLE 포맷으로 변환"""
    type_mapping = {
        'ticker': convert_ticker_default_to_simple,
        'trade': convert_trade_default_to_simple,
        'orderbook': convert_orderbook_default_to_simple,
        'candle': convert_candle_default_to_simple,
        'myorder': convert_myorder_default_to_simple,
        'myasset': convert_myasset_default_to_simple,
    }
    converter = type_mapping.get(data_type.lower())
    if not converter:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")
    return converter(data)


def convert_from_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    type_mapping = {
        'ticker': convert_ticker_simple_to_default,
        'trade': convert_trade_simple_to_default,
        'orderbook': convert_orderbook_simple_to_default,
        'candle': convert_candle_simple_to_default,
        'myorder': convert_myorder_simple_to_default,
        'myasset': convert_myasset_simple_to_default,
    }
    converter = type_mapping.get(data_type.lower())
    if not converter:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")
    return converter(data)


def auto_detect_and_convert(data: Dict[str, Any]) -> Dict[str, Any]:
    """자동으로 포맷을 감지하고 반대 포맷으로 변환"""
    # 타입별 감지 및 변환
    type_checks = [
        ('ticker', lambda d: ('ty' in d and d['ty'] == 'ticker') or ('type' in d and d['type'] == 'ticker')),
        ('trade', lambda d: ('ty' in d and d['ty'] == 'trade') or ('type' in d and d['type'] == 'trade')),
        ('orderbook', lambda d: ('ty' in d and d['ty'] == 'orderbook') or ('type' in d and d['type'] == 'orderbook')),
        ('candle', lambda d: ('ty' in d and str(d['ty']).startswith('candle'))
         or ('type' in d and str(d['type']).startswith('candle'))),
        ('myorder', lambda d: ('ty' in d and d['ty'] == 'myOrder') or ('type' in d and d['type'] == 'myOrder')),
        ('myasset', lambda d: ('ty' in d and d['ty'] == 'myAsset') or ('type' in d and d['type'] == 'myAsset')),
    ]

    for data_type, check_func in type_checks:
        if check_func(data):
            format_detectors = {
                'ticker': detect_ticker_format,
                'trade': detect_trade_format,
                'orderbook': detect_orderbook_format,
                'candle': detect_candle_format,
                'myorder': detect_myorder_format,
                'myasset': detect_myasset_format,
            }
            current_format = format_detectors[data_type](data)
            if current_format == "SIMPLE":
                return convert_from_simple_format(data, data_type)
            else:
                return convert_to_simple_format(data, data_type)

    raise ValueError("알 수 없는 WebSocket 메시지 타입입니다.")


# ================================================================
# 통합 테스트
# ================================================================


def test_all_simple_conversions():
    """모든 SIMPLE 포맷 변환 통합 테스트"""
    print("\n🧪 통합 SIMPLE 포맷 변환 테스트")
    print("=" * 60)

    examples = {
        'ticker': {
            'ty': 'ticker', 'cd': 'KRW-BTC', 'tp': 95500000.0, 'op': 95000000.0,
            'hp': 96000000.0, 'lp': 94000000.0, 'c': 'RISE', 'st': 'REALTIME'
        },
        'trade': {
            'ty': 'trade', 'cd': 'KRW-BTC', 'tp': 95500000.0, 'tv': 0.1,
            'ab': 'BID', 'sid': 123456789, 'st': 'REALTIME'
        },
        'orderbook': {
            'ty': 'orderbook', 'cd': 'KRW-BTC', 'tas': 4.79, 'tbs': 2.66,
            'obu': [{'ap': 137002000, 'bp': 137001000, 'as': 0.106, 'bs': 0.036}],
            'st': 'SNAPSHOT'
        },
        'candle': {
            'ty': 'candle', 'cd': 'KRW-BTC', 'op': 95000000.0, 'hp': 96000000.0,
            'lp': 94000000.0, 'tp': 95500000.0, 'catv': 10.5, 'catp': 1000000000.0,
            'st': 'REALTIME'
        },
        'myorder': {
            'ty': 'myOrder', 'cd': 'KRW-BTC', 'uid': 'ac2dc2a3-fce9-40a2-a4f6-5987c25c438f',
            'ab': 'BID', 'ot': 'limit', 's': 'trade', 'p': 95000000.0, 'v': 0.1,
            'st': 'REALTIME'
        },
        'myasset': {
            'ty': 'myAsset', 'astuid': 'e635f223-1609-4969-8fb6-4376937baad6',
            'ast': [{'cu': 'KRW', 'b': 1386929.37, 'l': 10329.67}],
            'asttms': 1710146517259, 'st': 'REALTIME'
        },
    }

    for data_type, simple_data in examples.items():
        print(f"\n📋 {data_type.upper()} 테스트:")
        print("-" * 30)

        try:
            # SIMPLE → DEFAULT 변환
            default_data = convert_from_simple_format(simple_data, data_type)
            print(f"✅ DEFAULT 변환: {default_data.get('type')} / {default_data.get('code')}")

            # DEFAULT → SIMPLE 재변환 (라운드트립)
            simple_again = convert_to_simple_format(default_data, data_type)
            print(f"✅ SIMPLE 재변환: {simple_again.get('ty')} / {simple_again.get('cd')}")

            # 자동 감지 변환
            auto_converted = auto_detect_and_convert(simple_data)
            print(f"✅ 자동 변환: {auto_converted.get('type')} 포맷으로 변환 완료")

        except Exception as e:
            print(f"❌ {data_type} 테스트 실패: {e}")

    print("\n🎯 통합 테스트 완료!")


if __name__ == "__main__":
    test_all_simple_conversions()
