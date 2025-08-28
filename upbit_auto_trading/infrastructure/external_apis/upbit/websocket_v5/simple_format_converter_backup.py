
"""
업비트 WebSocket v5.0 - SIMPLE 포맷 변환기

🎯 특징:
- 업비트 공식 SIMPLE 포맷 지원 (압축 전송용)
- 양방향 변환: DEFAULT ↔ SIMPLE
- 자동 포맷 감지 및 검증
- 모든 WebSocket 데이터 타입 지원 (Ticker, Trade, Orderbook, Candle)
"""

from typing import Dict, Any

# ================================================================
# SIMPLE 포맷 변환 기능 (업비트 최적화 지원)
# ================================================================

# ================================================================
# TICKER SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

# 📋 Ticker SIMPLE 포맷 필드 매핑 (https://docs.upbit.com/kr/reference/websocket-ticker)
TICKER_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty',                           # 데이터 항목
    'code': 'cd',                           # 페어 코드
    'timestamp': 'tms',                     # 타임스탬프 (ms)
    'stream_type': 'st',                    # 스트림 타입 (SNAPSHOT/REALTIME)

    # 💰 가격 정보 (OHLC + 현재가)
    'opening_price': 'op',                  # 시가
    'high_price': 'hp',                     # 고가
    'low_price': 'lp',                      # 저가
    'trade_price': 'tp',                    # 현재가
    'prev_closing_price': 'pcp',            # 전일 종가

    # 📈 변화량 정보
    'change': 'c',                          # 전일 종가 대비 가격 변동 방향
    'change_price': 'cp',                   # 전일 대비 가격 변동의 절대값
    'signed_change_price': 'scp',           # 전일 대비 가격 변동 값
    'change_rate': 'cr',                    # 전일 대비 등락율의 절대값
    'signed_change_rate': 'scr',            # 전일 대비 등락율

    # 📊 거래량 정보
    'trade_volume': 'tv',                   # 가장 최근 거래량
    'acc_trade_volume': 'atv',              # 누적 거래량(UTC 0시 기준)
    'acc_trade_volume_24h': 'atv24h',       # 24시간 누적 거래량
    'acc_trade_price': 'atp',               # 누적 거래대금(UTC 0시 기준)
    'acc_trade_price_24h': 'atp24h',        # 24시간 누적 거래대금

    # ⏰ 거래 시각 정보
    'trade_date': 'tdt',                    # 최근 거래 일자(UTC) - yyyyMMdd
    'trade_time': 'ttm',                    # 최근 거래 시각(UTC) - HHmmss
    'trade_timestamp': 'ttms',              # 체결 타임스탬프(ms)

    # 🎯 매수/매도 구분
    'ask_bid': 'ab',                        # 매수/매도 구분 (ASK: 매도, BID: 매수)

    # 📈 누적량 분석
    'acc_ask_volume': 'aav',                # 누적 매도량
    'acc_bid_volume': 'abv',                # 누적 매수량

    # 🏆 52주 최고/최저 (연간 통계)
    'highest_52_week_price': 'h52wp',       # 52주 최고가
    'highest_52_week_date': 'h52wdt',       # 52주 최고가 달성일 (yyyy-MM-dd)
    'lowest_52_week_price': 'l52wp',        # 52주 최저가
    'lowest_52_week_date': 'l52wdt',        # 52주 최저가 달성일 (yyyy-MM-dd)

    # 🎯 시장 상태 정보
    'market_state': 'ms',                   # 거래상태 (PREVIEW/ACTIVE/DELISTED)
    'market_state_for_ios': 'msfi',         # 거래 상태 (Deprecated)
    'is_trading_suspended': 'its',          # 거래 정지 여부 (Deprecated)
    'delisting_date': 'dd',                 # 거래지원 종료일
    'market_warning': 'mw',                 # 유의 종목 여부 (NONE/CAUTION)
    'trade_status': 'ts',                   # 거래상태 (Deprecated)
}

# 📋 Ticker SIMPLE 포맷 역매핑 (SIMPLE → DEFAULT 변환용)
TICKER_SIMPLE_REVERSE_MAPPING = {v: k for k, v in TICKER_SIMPLE_MAPPING.items()}


# ================================================================
# SIMPLE 포맷 변환 함수들 (Ticker 전용)
# ================================================================

def convert_ticker_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ticker SIMPLE 포맷을 DEFAULT 포맷으로 변환

    Args:
        data: SIMPLE 포맷 ticker 데이터

    Returns:
        Dict: DEFAULT 포맷으로 변환된 데이터
    """
    converted = {}

    for simple_key, value in data.items():
        # SIMPLE 키를 DEFAULT 키로 변환
        default_key = TICKER_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        converted[default_key] = value

    return converted


def convert_ticker_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ticker DEFAULT 포맷을 SIMPLE 포맷으로 변환

    Args:
        data: DEFAULT 포맷 ticker 데이터

    Returns:
        Dict: SIMPLE 포맷으로 변환된 데이터
    """
    converted = {}

    for default_key, value in data.items():
        # DEFAULT 키를 SIMPLE 키로 변환
        simple_key = TICKER_SIMPLE_MAPPING.get(default_key, default_key)
        converted[simple_key] = value

    return converted


def detect_ticker_format(data: Dict[str, Any]) -> str:
    """
    Ticker 메시지 포맷 감지 (DEFAULT vs SIMPLE)

    Args:
        data: ticker 메시지 데이터

    Returns:
        str: "DEFAULT" 또는 "SIMPLE"
    """
    # SIMPLE 포맷 고유 키들로 판단
    simple_indicators = ['ty', 'cd', 'tp', 'op', 'hp', 'lp']
    default_indicators = ['type', 'code', 'trade_price', 'opening_price']

    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)

    if simple_count > default_count:
        return "SIMPLE"
    else:
        return "DEFAULT"


def validate_ticker_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ticker SIMPLE 포맷 데이터 검증

    Args:
        data: SIMPLE 포맷 ticker 데이터

    Returns:
        Dict: 검증된 데이터
    """
    # 필수 SIMPLE 필드 검증
    required_simple_fields = ['cd', 'tp']  # code, trade_price
    for field in required_simple_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Ticker SIMPLE 필수 필드 누락: {field}")

    # 가격 필드 양수 검증
    price_fields = ['op', 'hp', 'lp', 'tp', 'pcp']  # opening, high, low, trade, prev_closing
    for field in price_fields:
        if field in data and data[field] is not None:
            try:
                if float(data[field]) <= 0:
                    raise ValueError(f"Ticker SIMPLE 가격 필드는 양수여야 함: {field}={data[field]}")
            except (ValueError, TypeError):
                raise ValueError(f"Ticker SIMPLE 가격 필드 타입 오류: {field}={data[field]}")

    return data


# ================================================================
# 사용 예시 및 테스트 (Ticker SIMPLE 포맷)
# ================================================================

def example_ticker_simple_message() -> Dict[str, Any]:
    """Ticker SIMPLE 포맷 메시지 예시"""
    return {
        'ty': 'ticker',           # type
        'cd': 'KRW-BTC',         # code
        'op': 95000000.0,        # opening_price
        'hp': 96000000.0,        # high_price
        'lp': 94000000.0,        # low_price
        'tp': 95500000.0,        # trade_price
        'pcp': 95000000.0,       # prev_closing_price
        'c': 'RISE',             # change
        'cp': 500000.0,          # change_price
        'cr': 0.0053,            # change_rate
        'tv': 0.1,               # trade_volume
        'atp24h': 1000000000.0,  # acc_trade_price_24h
        'atv24h': 10.5,          # acc_trade_volume_24h
        'tms': 1640995200000,    # timestamp
        'st': 'REALTIME'         # stream_type
    }


def test_ticker_simple_conversion():
    """Ticker SIMPLE 포맷 변환 테스트"""
    print("\n🧪 Ticker SIMPLE 포맷 변환 테스트")
    print("=" * 50)

    # 1. SIMPLE 예시 메시지
    simple_data = example_ticker_simple_message()
    print("📨 SIMPLE 포맷 원본:")
    print(f"   {simple_data}")

    # 2. 포맷 감지 테스트
    detected_format = detect_ticker_format(simple_data)
    print(f"🔍 감지된 포맷: {detected_format}")

    # 3. SIMPLE → DEFAULT 변환
    default_data = convert_ticker_simple_to_default(simple_data)
    print("🔄 DEFAULT 포맷 변환 결과:")
    print(f"   type: {default_data.get('type')}")
    print(f"   code: {default_data.get('code')}")
    print(f"   trade_price: {default_data.get('trade_price')}")
    print(f"   change: {default_data.get('change')}")

    # 4. DEFAULT → SIMPLE 재변환 (라운드트립 테스트)
    simple_again = convert_ticker_default_to_simple(default_data)
    print("🔄 SIMPLE 재변환 결과:")
    print(f"   ty: {simple_again.get('ty')}")
    print(f"   cd: {simple_again.get('cd')}")
    print(f"   tp: {simple_again.get('tp')}")

    # 5. 검증 테스트
    try:
        validated = validate_ticker_simple_format(simple_data)
        print("✅ SIMPLE 포맷 검증 성공")
    except Exception as e:
        print(f"❌ SIMPLE 포맷 검증 실패: {e}")


if __name__ == "__main__":
    # Ticker SIMPLE 포맷 테스트 실행
    test_ticker_simple_conversion()


# ================================================================
# ORDERBOOK SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

# 📋 Orderbook SIMPLE 포맷 필드 매핑 (https://docs.upbit.com/kr/reference/websocket-orderbook)
ORDERBOOK_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty',                           # 타입
    'code': 'cd',                           # 마켓 코드
    'timestamp': 'tms',                     # 타임스탬프 (ms)
    'stream_type': 'st',                    # 스트림 타입 (SNAPSHOT/REALTIME)

    # 📊 총 잔량 정보
    'total_ask_size': 'tas',                # 호가 매도 총 잔량
    'total_bid_size': 'tbs',                # 호가 매수 총 잔량

    # 🏢 호가 데이터 배열
    'orderbook_units': 'obu',               # 호가 배열

    # 🔢 호가 모아보기 설정
    'level': 'lv',                          # 호가 모아보기 단위 (default: 0, 기본 호가단위)
}

# 📋 Orderbook Units 내부 필드 SIMPLE 매핑 (각 호가 레벨의 필드들)
ORDERBOOK_UNITS_SIMPLE_MAPPING = {
    # 💰 호가 가격
    'ask_price': 'ap',                      # 매도 호가
    'bid_price': 'bp',                      # 매수 호가

    # 📊 호가 잔량
    'ask_size': 'as',                       # 매도 잔량
    'bid_size': 'bs',                       # 매수 잔량
}

# 📋 Orderbook SIMPLE 포맷 역매핑 (SIMPLE → DEFAULT 변환용)
ORDERBOOK_SIMPLE_REVERSE_MAPPING = {v: k for k, v in ORDERBOOK_SIMPLE_MAPPING.items()}
ORDERBOOK_UNITS_SIMPLE_REVERSE_MAPPING = {v: k for k, v in ORDERBOOK_UNITS_SIMPLE_MAPPING.items()}


# ================================================================
# SIMPLE 포맷 변환 함수들 (Orderbook 전용)
# ================================================================

def convert_orderbook_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orderbook SIMPLE 포맷을 DEFAULT 포맷으로 변환

    Args:
        data: SIMPLE 포맷 orderbook 데이터

    Returns:
        Dict: DEFAULT 포맷으로 변환된 데이터
    """
    converted = {}

    for simple_key, value in data.items():
        # 메인 필드 변환
        default_key = ORDERBOOK_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)

        # orderbook_units 배열 내부 필드 변환
        if simple_key == 'obu' and isinstance(value, list):
            converted_units = []
            for unit in value:
                if isinstance(unit, dict):
                    converted_unit = {}
                    for unit_simple_key, unit_value in unit.items():
                        unit_default_key = ORDERBOOK_UNITS_SIMPLE_REVERSE_MAPPING.get(unit_simple_key, unit_simple_key)
                        converted_unit[unit_default_key] = unit_value
                    converted_units.append(converted_unit)
                else:
                    converted_units.append(unit)
            converted[default_key] = converted_units
        else:
            converted[default_key] = value

    return converted


def convert_orderbook_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orderbook DEFAULT 포맷을 SIMPLE 포맷으로 변환

    Args:
        data: DEFAULT 포맷 orderbook 데이터

    Returns:
        Dict: SIMPLE 포맷으로 변환된 데이터
    """
    converted = {}

    for default_key, value in data.items():
        # 메인 필드 변환
        simple_key = ORDERBOOK_SIMPLE_MAPPING.get(default_key, default_key)

        # orderbook_units 배열 내부 필드 변환
        if default_key == 'orderbook_units' and isinstance(value, list):
            converted_units = []
            for unit in value:
                if isinstance(unit, dict):
                    converted_unit = {}
                    for unit_default_key, unit_value in unit.items():
                        unit_simple_key = ORDERBOOK_UNITS_SIMPLE_MAPPING.get(unit_default_key, unit_default_key)
                        converted_unit[unit_simple_key] = unit_value
                    converted_units.append(converted_unit)
                else:
                    converted_units.append(unit)
            converted[simple_key] = converted_units
        else:
            converted[simple_key] = value

    return converted


def detect_orderbook_format(data: Dict[str, Any]) -> str:
    """
    Orderbook 메시지 포맷 감지 (DEFAULT vs SIMPLE)

    Args:
        data: orderbook 메시지 데이터

    Returns:
        str: "DEFAULT" 또는 "SIMPLE"
    """
    # SIMPLE 포맷 고유 키들로 판단
    simple_indicators = ['ty', 'cd', 'tas', 'tbs', 'obu']
    default_indicators = ['type', 'code', 'total_ask_size', 'total_bid_size', 'orderbook_units']

    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)

    if simple_count > default_count:
        return "SIMPLE"
    else:
        return "DEFAULT"


def validate_orderbook_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orderbook SIMPLE 포맷 데이터 검증

    Args:
        data: SIMPLE 포맷 orderbook 데이터

    Returns:
        Dict: 검증된 데이터
    """
    # 필수 SIMPLE 필드 검증
    required_simple_fields = ['cd', 'obu']  # code, orderbook_units
    for field in required_simple_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Orderbook SIMPLE 필수 필드 누락: {field}")

    # orderbook_units 배열 검증
    orderbook_units = data['obu']
    if not isinstance(orderbook_units, list) or len(orderbook_units) == 0:
        raise ValueError("Orderbook SIMPLE 호가 정보가 비어있음")

    # 각 호가 레벨 검증
    for i, unit in enumerate(orderbook_units):
        if not isinstance(unit, dict):
            raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 타입 오류: dict 필요")

        unit_required = ['ap', 'bp', 'as', 'bs']  # ask_price, bid_price, ask_size, bid_size
        for field in unit_required:
            if field not in unit or unit[field] is None:
                raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 필수 필드 누락: {field}")

            # 가격/수량 양수 검증
            try:
                if float(unit[field]) < 0:
                    raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 필드는 음수 불가: {field}={unit[field]}")
            except (ValueError, TypeError):
                raise ValueError(f"Orderbook SIMPLE 호가 레벨 {i} 필드 타입 오류: {field}={unit[field]}")

    return data


# ================================================================
# 사용 예시 및 테스트 (Orderbook SIMPLE 포맷)
# ================================================================

def example_orderbook_simple_message() -> Dict[str, Any]:
    """Orderbook SIMPLE 포맷 메시지 예시"""
    return {
        'ty': 'orderbook',           # type
        'cd': 'KRW-BTC',            # code
        'tms': 1746601573804,       # timestamp
        'tas': 4.79158413,          # total_ask_size
        'tbs': 2.65609625,          # total_bid_size
        'obu': [                    # orderbook_units
            {
                'ap': 137002000,    # ask_price
                'bp': 137001000,    # bid_price
                'as': 0.10623869,   # ask_size
                'bs': 0.03656812    # bid_size
            },
            {
                'ap': 137023000,    # ask_price
                'bp': 137000000,    # bid_price
                'as': 0.06144079,   # ask_size
                'bs': 0.33543284    # bid_size
            }
        ],
        'lv': 0,                    # level
        'st': 'SNAPSHOT'            # stream_type
    }


def test_orderbook_simple_conversion():
    """Orderbook SIMPLE 포맷 변환 테스트"""
    print("\n🧪 Orderbook SIMPLE 포맷 변환 테스트")
    print("=" * 50)

    # 1. SIMPLE 예시 메시지
    simple_data = example_orderbook_simple_message()
    print("📨 SIMPLE 포맷 원본:")
    print(f"   ty: {simple_data.get('ty')}")
    print(f"   cd: {simple_data.get('cd')}")
    print(f"   tas: {simple_data.get('tas')}")
    print(f"   obu[0]: {simple_data.get('obu', [{}])[0] if simple_data.get('obu') else 'None'}")

    # 2. 포맷 감지 테스트
    detected_format = detect_orderbook_format(simple_data)
    print(f"🔍 감지된 포맷: {detected_format}")

    # 3. SIMPLE → DEFAULT 변환
    default_data = convert_orderbook_simple_to_default(simple_data)
    print("🔄 DEFAULT 포맷 변환 결과:")
    print(f"   type: {default_data.get('type')}")
    print(f"   code: {default_data.get('code')}")
    print(f"   total_ask_size: {default_data.get('total_ask_size')}")
    units = default_data.get('orderbook_units', [])
    print(f"   orderbook_units[0]: {units[0] if units else 'None'}")

    # 4. DEFAULT → SIMPLE 재변환 (라운드트립 테스트)
    simple_again = convert_orderbook_default_to_simple(default_data)
    print("🔄 SIMPLE 재변환 결과:")
    print(f"   ty: {simple_again.get('ty')}")
    print(f"   cd: {simple_again.get('cd')}")
    print(f"   tas: {simple_again.get('tas')}")

    # 5. 검증 테스트
    try:
        validated = validate_orderbook_simple_format(simple_data)
        print("✅ SIMPLE 포맷 검증 성공")
    except Exception as e:
        print(f"❌ SIMPLE 포맷 검증 실패: {e}")


# 테스트 실행 (개발 중에만)
if __name__ == "__main__":
    # Ticker SIMPLE 포맷 테스트 실행
    test_ticker_simple_conversion()

    # Orderbook SIMPLE 포맷 테스트 실행
    test_orderbook_simple_conversion()


# ================================================================
# TRADE SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

# 📋 Trade SIMPLE 포맷 필드 매핑 (https://docs.upbit.com/kr/reference/websocket-trade)
TRADE_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty',                           # 데이터 항목
    'code': 'cd',                           # 페어 코드
    'timestamp': 'tms',                     # 타임스탬프 (ms)
    'stream_type': 'st',                    # 스트림 타입 (SNAPSHOT/REALTIME)

    # 💰 체결 정보
    'trade_price': 'tp',                    # 체결 가격
    'trade_volume': 'tv',                   # 체결량
    'ask_bid': 'ab',                        # 매수/매도 구분 (ASK: 매도, BID: 매수)
    'prev_closing_price': 'pcp',            # 전일 종가

    # 📈 변화 정보
    'change': 'c',                          # 전일 종가 대비 가격 변동 방향 (RISE/EVEN/FALL)
    'change_price': 'cp',                   # 전일 대비 가격 변동의 절대값

    # ⏰ 체결 시각 정보
    'trade_date': 'td',                     # 체결 일자(UTC 기준) - yyyy-MM-dd
    'trade_time': 'ttm',                    # 체결 시각(UTC 기준) - HH:mm:ss
    'trade_timestamp': 'ttms',              # 체결 타임스탬프(ms)

    # 🔢 체결 고유번호
    'sequential_id': 'sid',                 # 체결 번호(Unique)

    # 🏆 최우선 호가 정보
    'best_ask_price': 'bap',                # 최우선 매도 호가
    'best_ask_size': 'bas',                 # 최우선 매도 잔량
    'best_bid_price': 'bbp',                # 최우선 매수 호가
    'best_bid_size': 'bbs',                 # 최우선 매수 잔량
}

# 📋 Trade SIMPLE 포맷 역매핑 (SIMPLE → DEFAULT 변환용)
TRADE_SIMPLE_REVERSE_MAPPING = {v: k for k, v in TRADE_SIMPLE_MAPPING.items()}


# ================================================================
# SIMPLE 포맷 변환 함수들 (Trade 전용)
# ================================================================

def convert_trade_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    converted = {}
    for simple_key, value in data.items():
        default_key = TRADE_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        converted[default_key] = value
    return converted


def convert_trade_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade DEFAULT 포맷을 SIMPLE 포맷으로 변환"""
    converted = {}
    for default_key, value in data.items():
        simple_key = TRADE_SIMPLE_MAPPING.get(default_key, default_key)
        converted[simple_key] = value
    return converted


def detect_trade_format(data: Dict[str, Any]) -> str:
    """Trade 메시지 포맷 감지 (DEFAULT vs SIMPLE)"""
    simple_indicators = ['ty', 'cd', 'tp', 'tv', 'ab', 'sid']
    default_indicators = ['type', 'code', 'trade_price', 'trade_volume', 'ask_bid', 'sequential_id']

    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)

    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def validate_trade_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Trade SIMPLE 포맷 데이터 검증"""
    # 필수 SIMPLE 필드 검증
    required_simple_fields = ['cd', 'tp', 'tv', 'ab', 'sid']
    for field in required_simple_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Trade SIMPLE 필수 필드 누락: {field}")

    # 매수/매도 구분 검증
    if data['ab'] not in ['ASK', 'BID']:
        raise ValueError(f"Trade SIMPLE 매수/매도 구분 오류: {data['ab']} (ASK/BID만 허용)")

    # 체결가/체결량 양수 검증
    if float(data['tp']) <= 0:
        raise ValueError(f"Trade SIMPLE 체결가는 양수여야 함: {data['tp']}")
    if float(data['tv']) <= 0:
        raise ValueError(f"Trade SIMPLE 체결량은 양수여야 함: {data['tv']}")

    return data


# ================================================================
# CANDLE SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

# 📋 Candle SIMPLE 포맷 필드 매핑 (https://docs.upbit.com/kr/reference/websocket-candle)
CANDLE_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty',                           # 데이터 항목 (candle)
    'code': 'cd',                           # 마켓 코드 (예: KRW-BTC)
    'timestamp': 'tms',                     # 타임스탬프 (ms)
    'stream_type': 'st',                    # 스트림 타입 (SNAPSHOT/REALTIME)

    # ⏰ 캔들 시간 정보
    'candle_date_time_utc': 'cdttmu',       # 캔들 기준 시각(UTC 기준) - ISO 8601 형식
    'candle_date_time_kst': 'cdttmk',       # 캔들 기준 시각(KST 기준) - ISO 8601 형식

    # 💰 OHLC 가격 정보
    'opening_price': 'op',                  # 시가
    'high_price': 'hp',                     # 고가
    'low_price': 'lp',                      # 저가
    'trade_price': 'tp',                    # 종가 (현재가)
    'prev_closing_price': 'pcp',            # 전일 종가

    # 📊 거래량 정보
    'candle_acc_trade_volume': 'catv',      # 누적 거래량
    'candle_acc_trade_price': 'catp',       # 누적 거래대금

    # 📈 변화 정보
    'change': 'c',                          # 전일 종가 대비 변화 방향 (RISE/EVEN/FALL)
    'change_price': 'cp',                   # 전일 대비 가격 변화의 절대값
    'change_rate': 'cr',                    # 전일 대비 등락율의 절대값
    'signed_change_price': 'scp',           # 전일 대비 가격 변화 (부호 포함)
    'signed_change_rate': 'scr',            # 전일 대비 등락율 (부호 포함)

    # 🎯 캔들 단위별 고유 정보
    'unit': 'u',                            # 캔들 단위 (1, 3, 5, 15, 30, 60, 240 등)
}

# 📋 Candle SIMPLE 포맷 역매핑 (SIMPLE → DEFAULT 변환용)
CANDLE_SIMPLE_REVERSE_MAPPING = {v: k for k, v in CANDLE_SIMPLE_MAPPING.items()}


# ================================================================
# SIMPLE 포맷 변환 함수들 (Candle 전용)
# ================================================================

def convert_candle_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    converted = {}
    for simple_key, value in data.items():
        default_key = CANDLE_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        converted[default_key] = value
    return converted


def convert_candle_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle DEFAULT 포맷을 SIMPLE 포맷으로 변환"""
    converted = {}
    for default_key, value in data.items():
        simple_key = CANDLE_SIMPLE_MAPPING.get(default_key, default_key)
        converted[simple_key] = value
    return converted


def detect_candle_format(data: Dict[str, Any]) -> str:
    """Candle 메시지 포맷 감지 (DEFAULT vs SIMPLE)"""
    simple_indicators = ['ty', 'cd', 'cdttmu', 'op', 'hp', 'lp', 'tp', 'catv']
    default_indicators = ['type', 'code', 'candle_date_time_utc', 'opening_price',
                          'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']

    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)

    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def validate_candle_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """Candle SIMPLE 포맷 데이터 검증"""
    # 필수 SIMPLE 필드 검증
    required_simple_fields = ['cd', 'op', 'hp', 'lp', 'tp', 'catv', 'catp']
    for field in required_simple_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Candle SIMPLE 필수 필드 누락: {field}")

    # OHLC 가격 필드 양수 검증
    price_fields = ['op', 'hp', 'lp', 'tp']
    for field in price_fields:
        try:
            if float(data[field]) <= 0:
                raise ValueError(f"Candle SIMPLE 가격 필드는 양수여야 함: {field}={data[field]}")
        except (ValueError, TypeError):
            raise ValueError(f"Candle SIMPLE 가격 필드 타입 오류: {field}={data[field]}")

    # OHLC 논리적 검증 (고가 >= 시가,종가,저가, 저가 <= 시가,종가,고가)
    try:
        op, hp, lp, tp = float(data['op']), float(data['hp']), float(data['lp']), float(data['tp'])
        if not (lp <= op <= hp and lp <= tp <= hp):
            raise ValueError(f"Candle SIMPLE OHLC 논리 오류: O={op}, H={hp}, L={lp}, C={tp}")
    except (ValueError, TypeError):
        raise ValueError("Candle SIMPLE OHLC 필드 값이 숫자가 아님")

    # 거래량/거래대금 음수 검증
    volume_fields = ['catv', 'catp']
    for field in volume_fields:
        try:
            if float(data[field]) < 0:
                raise ValueError(f"Candle SIMPLE 거래량 필드는 음수 불가: {field}={data[field]}")
        except (ValueError, TypeError):
            raise ValueError(f"Candle SIMPLE 거래량 필드 타입 오류: {field}={data[field]}")

    return data


# ================================================================
# 사용 예시 및 테스트 (Candle SIMPLE 포맷)
# ================================================================

def example_candle_simple_message() -> Dict[str, Any]:
    """Candle SIMPLE 포맷 메시지 예시"""
    return {
        'ty': 'candle',                  # type
        'cd': 'KRW-BTC',                # code
        'cdttmu': '2025-01-01T00:00:00Z',  # candle_date_time_utc
        'op': 95000000.0,               # opening_price
        'hp': 96000000.0,               # high_price
        'lp': 94000000.0,               # low_price
        'tp': 95500000.0,               # trade_price (종가)
        'pcp': 95000000.0,              # prev_closing_price
        'catv': 10.5,                   # candle_acc_trade_volume
        'catp': 1000000000.0,           # candle_acc_trade_price
        'c': 'RISE',                    # change
        'cp': 500000.0,                 # change_price
        'cr': 0.0053,                   # change_rate
        'tms': 1640995200000,           # timestamp
        'st': 'REALTIME',               # stream_type
        'u': 60                         # unit (60분봉)
    }


def test_candle_simple_conversion():
    """Candle SIMPLE 포맷 변환 테스트"""
    print("\n🧪 Candle SIMPLE 포맷 변환 테스트")
    print("=" * 50)

    # 1. SIMPLE 예시 메시지
    simple_data = example_candle_simple_message()
    print("📨 SIMPLE 포맷 원본:")
    print(f"   ty: {simple_data.get('ty')}")
    print(f"   cd: {simple_data.get('cd')}")
    ohlc = f"O={simple_data.get('op')}, H={simple_data.get('hp')}, L={simple_data.get('lp')}, C={simple_data.get('tp')}"
    print(f"   OHLC: {ohlc}")
    print(f"   catv: {simple_data.get('catv')}, unit: {simple_data.get('u')}")

    # 2. 포맷 감지 테스트
    detected_format = detect_candle_format(simple_data)
    print(f"🔍 감지된 포맷: {detected_format}")

    # 3. SIMPLE → DEFAULT 변환
    default_data = convert_candle_simple_to_default(simple_data)
    print("🔄 DEFAULT 포맷 변환 결과:")
    print(f"   type: {default_data.get('type')}")
    print(f"   code: {default_data.get('code')}")
    print(f"   candle_date_time_utc: {default_data.get('candle_date_time_utc')}")
    ohlc_default = f"O={default_data.get('opening_price')}, H={default_data.get('high_price')}, " \
                   f"L={default_data.get('low_price')}, C={default_data.get('trade_price')}"
    print(f"   OHLC: {ohlc_default}")

    # 4. DEFAULT → SIMPLE 재변환 (라운드트립 테스트)
    simple_again = convert_candle_default_to_simple(default_data)
    print("🔄 SIMPLE 재변환 결과:")
    print(f"   ty: {simple_again.get('ty')}")
    print(f"   cd: {simple_again.get('cd')}")
    ohlc_again = f"O={simple_again.get('op')}, H={simple_again.get('hp')}, " \
                 f"L={simple_again.get('lp')}, C={simple_again.get('tp')}"
    print(f"   OHLC: {ohlc_again}")

    # 5. 검증 테스트
    try:
        validate_candle_simple_format(simple_data)
        print("✅ SIMPLE 포맷 검증 성공")
    except Exception as e:
        print(f"❌ SIMPLE 포맷 검증 실패: {e}")


# ================================================================
# 통합 SIMPLE 포맷 변환기
# ================================================================

def convert_to_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 적절한 SIMPLE 포맷으로 변환"""
    if data_type.lower() == 'ticker':
        return convert_ticker_default_to_simple(data)
    elif data_type.lower() == 'trade':
        return convert_trade_default_to_simple(data)
    elif data_type.lower() == 'orderbook':
        return convert_orderbook_default_to_simple(data)
    elif data_type.lower().startswith('candle'):
        return convert_candle_default_to_simple(data)
    else:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")


def convert_from_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    if data_type.lower() == 'ticker':
        return convert_ticker_simple_to_default(data)
    elif data_type.lower() == 'trade':
        return convert_trade_simple_to_default(data)
    elif data_type.lower() == 'orderbook':
        return convert_orderbook_simple_to_default(data)
    elif data_type.lower().startswith('candle'):
        return convert_candle_simple_to_default(data)
    else:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")


def auto_detect_and_convert(data: Dict[str, Any]) -> Dict[str, Any]:
    """자동으로 포맷을 감지하고 반대 포맷으로 변환"""
    # 각 타입별로 포맷 감지 시도

    # Ticker 감지 및 변환
    if 'ty' in data and data['ty'] == 'ticker' or 'type' in data and data['type'] == 'ticker':
        current_format = detect_ticker_format(data)
        if current_format == "SIMPLE":
            return convert_ticker_simple_to_default(data)
        else:
            return convert_ticker_default_to_simple(data)

    # Trade 감지 및 변환
    elif 'ty' in data and data['ty'] == 'trade' or 'type' in data and data['type'] == 'trade':
        current_format = detect_trade_format(data)
        if current_format == "SIMPLE":
            return convert_trade_simple_to_default(data)
        else:
            return convert_trade_default_to_simple(data)

    # Orderbook 감지 및 변환
    elif 'ty' in data and data['ty'] == 'orderbook' or 'type' in data and data['type'] == 'orderbook':
        current_format = detect_orderbook_format(data)
        if current_format == "SIMPLE":
            return convert_orderbook_simple_to_default(data)
        else:
            return convert_orderbook_default_to_simple(data)

    # Candle 감지 및 변환
    elif (('ty' in data and str(data['ty']).startswith('candle'))
          or ('type' in data and str(data['type']).startswith('candle'))):
        current_format = detect_candle_format(data)
        if current_format == "SIMPLE":
            return convert_candle_simple_to_default(data)
        else:
            return convert_candle_default_to_simple(data)

    else:
        raise ValueError("알 수 없는 WebSocket 메시지 타입입니다.")


# ================================================================
# MYORDER SIMPLE 포맷 매핑 (업비트 공식 WebSocket 문서 기준)
# ================================================================

# 📋 MyOrder SIMPLE 포맷 필드 매핑 (https://docs.upbit.com/kr/reference/websocket-myorder)
MYORDER_SIMPLE_MAPPING = {
    # 🏷️ 기본 식별 정보
    'type': 'ty',                           # 타입 (myOrder)
    'code': 'cd',                           # 페어 코드 (예: KRW-BTC)
    'uuid': 'uid',                          # 주문의 유일 식별자
    'timestamp': 'tms',                     # 타임스탬프 (ms)
    'stream_type': 'st',                    # 스트림 타입 (REALTIME/SNAPSHOT)

    # 💰 주문 기본 정보
    'ask_bid': 'ab',                        # 매수/매도 구분 (ASK: 매도, BID: 매수)
    'order_type': 'ot',                     # 주문 타입 (limit/price/market/best)
    'state': 's',                           # 주문 상태 (wait/watch/trade/done/cancel/prevented)
    'trade_uuid': 'tuid',                   # 체결의 유일 식별자

    # 💲 가격 정보
    'price': 'p',                           # 주문 가격 또는 체결 가격 (state: trade 일 때)
    'avg_price': 'ap',                      # 평균 체결 가격
    'volume': 'v',                          # 주문량 또는 체결량 (state: trade 일 때)
    'remaining_volume': 'rv',               # 체결 후 주문 잔량
    'executed_volume': 'ev',                # 체결된 수량

    # 📊 체결 및 수수료 정보
    'trades_count': 'tc',                   # 해당 주문에 걸린 체결 수
    'reserved_fee': 'rsf',                  # 수수료로 예약된 비용
    'remaining_fee': 'rmf',                 # 남은 수수료
    'paid_fee': 'pf',                       # 사용된 수수료
    'locked': 'l',                          # 거래에 사용중인 비용
    'executed_funds': 'ef',                 # 체결된 금액
    'trade_fee': 'tf',                      # 체결 시 발생한 수수료 (state:trade가 아닐 경우 null)

    # 🎯 주문 조건 및 특성
    'time_in_force': 'tif',                 # IOC, FOK, POST ONLY 설정 (ioc/fok/post_only)
    'is_maker': 'im',                       # 체결이 발생한 주문의 메이커/테이커 여부 (true: 메이커, false: 테이커)
    'identifier': 'id',                     # 클라이언트 지정 주문 식별자

    # 🔒 자전거래 체결 방지 (SMP) 관련
    'smp_type': 'smpt',                     # 자전거래 체결 방지 타입 (reduce/cancel_maker/cancel_taker)
    'prevented_volume': 'pv',               # 자전거래 체결 방지로 인해 취소된 주문 수량
    'prevented_locked': 'pl',               # 자전거래 체결 방지 설정으로 인해 취소된 금액/수량

    # ⏰ 시간 정보
    'trade_timestamp': 'ttms',              # 체결 타임스탬프 (ms)
    'order_timestamp': 'otms',              # 주문 타임스탬프 (ms)
}

# 📋 MyOrder SIMPLE 포맷 역매핑 (SIMPLE → DEFAULT 변환용)
MYORDER_SIMPLE_REVERSE_MAPPING = {v: k for k, v in MYORDER_SIMPLE_MAPPING.items()}


# ================================================================
# SIMPLE 포맷 변환 함수들 (MyOrder 전용)
# ================================================================

def convert_myorder_simple_to_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    converted = {}
    for simple_key, value in data.items():
        default_key = MYORDER_SIMPLE_REVERSE_MAPPING.get(simple_key, simple_key)
        converted[default_key] = value
    return converted


def convert_myorder_default_to_simple(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder DEFAULT 포맷을 SIMPLE 포맷으로 변환"""
    converted = {}
    for default_key, value in data.items():
        simple_key = MYORDER_SIMPLE_MAPPING.get(default_key, default_key)
        converted[simple_key] = value
    return converted


def detect_myorder_format(data: Dict[str, Any]) -> str:
    """MyOrder 메시지 포맷 감지 (DEFAULT vs SIMPLE)"""
    simple_indicators = ['ty', 'cd', 'uid', 'ab', 'ot', 's', 'p', 'v']
    default_indicators = ['type', 'code', 'uuid', 'ask_bid', 'order_type', 'state', 'price', 'volume']

    simple_count = sum(1 for key in simple_indicators if key in data)
    default_count = sum(1 for key in default_indicators if key in data)

    return "SIMPLE" if simple_count > default_count else "DEFAULT"


def validate_myorder_simple_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """MyOrder SIMPLE 포맷 데이터 검증"""
    # 필수 SIMPLE 필드 검증
    required_simple_fields = ['cd', 'uid', 'ab', 'ot', 's']
    for field in required_simple_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"MyOrder SIMPLE 필수 필드 누락: {field}")

    # 매수/매도 구분 검증
    if data['ab'] not in ['ASK', 'BID']:
        raise ValueError(f"MyOrder SIMPLE 매수/매도 구분 오류: {data['ab']} (ASK/BID만 허용)")

    # 주문 타입 검증
    valid_order_types = ['limit', 'price', 'market', 'best']
    if data['ot'] not in valid_order_types:
        raise ValueError(f"MyOrder SIMPLE 주문 타입 오류: {data['ot']} ({'/'.join(valid_order_types)}만 허용)")

    # 주문 상태 검증
    valid_states = ['wait', 'watch', 'trade', 'done', 'cancel', 'prevented']
    if data['s'] not in valid_states:
        raise ValueError(f"MyOrder SIMPLE 주문 상태 오류: {data['s']} ({'/'.join(valid_states)}만 허용)")

    # 가격/수량 필드 양수 검증 (존재하는 경우)
    numeric_fields = ['p', 'ap', 'v', 'rv', 'ev', 'rsf', 'rmf', 'pf', 'l', 'ef', 'tf', 'pv', 'pl']
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                if float(data[field]) < 0:
                    raise ValueError(f"MyOrder SIMPLE 숫자 필드는 음수 불가: {field}={data[field]}")
            except (ValueError, TypeError):
                raise ValueError(f"MyOrder SIMPLE 숫자 필드 타입 오류: {field}={data[field]}")

    return data


# ================================================================
# 통합 SIMPLE 포맷 변환기 (업데이트)
# ================================================================

def convert_to_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 적절한 SIMPLE 포맷으로 변환"""
    if data_type.lower() == 'ticker':
        return convert_ticker_default_to_simple(data)
    elif data_type.lower() == 'trade':
        return convert_trade_default_to_simple(data)
    elif data_type.lower() == 'orderbook':
        return convert_orderbook_default_to_simple(data)
    elif data_type.lower().startswith('candle'):
        return convert_candle_default_to_simple(data)
    elif data_type.lower() == 'myorder':
        return convert_myorder_default_to_simple(data)
    else:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")


def convert_from_simple_format(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """데이터 타입에 따라 SIMPLE 포맷을 DEFAULT 포맷으로 변환"""
    if data_type.lower() == 'ticker':
        return convert_ticker_simple_to_default(data)
    elif data_type.lower() == 'trade':
        return convert_trade_simple_to_default(data)
    elif data_type.lower() == 'orderbook':
        return convert_orderbook_simple_to_default(data)
    elif data_type.lower().startswith('candle'):
        return convert_candle_simple_to_default(data)
    elif data_type.lower() == 'myorder':
        return convert_myorder_simple_to_default(data)
    else:
        raise ValueError(f"지원하지 않는 데이터 타입: {data_type}")


def auto_detect_and_convert(data: Dict[str, Any]) -> Dict[str, Any]:
    """자동으로 포맷을 감지하고 반대 포맷으로 변환"""
    # 각 타입별로 포맷 감지 시도

    # Ticker 감지 및 변환
    if 'ty' in data and data['ty'] == 'ticker' or 'type' in data and data['type'] == 'ticker':
        current_format = detect_ticker_format(data)
        if current_format == "SIMPLE":
            return convert_ticker_simple_to_default(data)
        else:
            return convert_ticker_default_to_simple(data)

    # Trade 감지 및 변환
    elif 'ty' in data and data['ty'] == 'trade' or 'type' in data and data['type'] == 'trade':
        current_format = detect_trade_format(data)
        if current_format == "SIMPLE":
            return convert_trade_simple_to_default(data)
        else:
            return convert_trade_default_to_simple(data)

    # Orderbook 감지 및 변환
    elif 'ty' in data and data['ty'] == 'orderbook' or 'type' in data and data['type'] == 'orderbook':
        current_format = detect_orderbook_format(data)
        if current_format == "SIMPLE":
            return convert_orderbook_simple_to_default(data)
        else:
            return convert_orderbook_default_to_simple(data)

    # Candle 감지 및 변환
    elif (('ty' in data and str(data['ty']).startswith('candle'))
          or ('type' in data and str(data['type']).startswith('candle'))):
        current_format = detect_candle_format(data)
        if current_format == "SIMPLE":
            return convert_candle_simple_to_default(data)
        else:
            return convert_candle_default_to_simple(data)

    # MyOrder 감지 및 변환
    elif 'ty' in data and data['ty'] == 'myOrder' or 'type' in data and data['type'] == 'myOrder':
        current_format = detect_myorder_format(data)
        if current_format == "SIMPLE":
            return convert_myorder_simple_to_default(data)
        else:
            return convert_myorder_default_to_simple(data)

    else:
        raise ValueError("알 수 없는 WebSocket 메시지 타입입니다.")


# ================================================================
# 통합 예제 및 테스트
# ================================================================

def example_all_simple_formats() -> Dict[str, Dict[str, Any]]:
    """모든 SIMPLE 포맷 예시 메시지 통합"""
    return {
        'ticker': {
            'ty': 'ticker', 'cd': 'KRW-BTC', 'tp': 95500000.0, 'op': 95000000.0,
            'hp': 96000000.0, 'lp': 94000000.0, 'c': 'RISE', 'cp': 500000.0,
            'tv': 0.1, 'atp24h': 1000000000.0, 'st': 'REALTIME'
        },
        'trade': {
            'ty': 'trade', 'cd': 'KRW-BTC', 'tp': 95500000.0, 'tv': 0.1,
            'ab': 'BID', 'pcp': 95000000.0, 'c': 'RISE', 'sid': 123456789,
            'st': 'REALTIME'
        },
        'orderbook': {
            'ty': 'orderbook', 'cd': 'KRW-BTC', 'tas': 4.79158413, 'tbs': 2.65609625,
            'obu': [{'ap': 137002000, 'bp': 137001000, 'as': 0.10623869, 'bs': 0.03656812}],
            'st': 'SNAPSHOT'
        },
        'candle': {
            'ty': 'candle', 'cd': 'KRW-BTC', 'op': 95000000.0, 'hp': 96000000.0,
            'lp': 94000000.0, 'tp': 95500000.0, 'catv': 10.5, 'catp': 1000000000.0,
            'c': 'RISE', 'u': 60, 'st': 'REALTIME'
        },
        'myorder': {
            'ty': 'myOrder', 'cd': 'KRW-BTC', 'uid': 'ac2dc2a3-fce9-40a2-a4f6-5987c25c438f',
            'ab': 'BID', 'ot': 'limit', 's': 'trade', 'p': 95000000.0, 'v': 0.1,
            'rv': 0.05, 'ev': 0.05, 'tc': 1, 'st': 'REALTIME'
        }
    }


def test_all_simple_conversions():
    """모든 SIMPLE 포맷 변환 통합 테스트"""
    print("\n🧪 통합 SIMPLE 포맷 변환 테스트")
    print("=" * 60)

    examples = example_all_simple_formats()

    for data_type, simple_data in examples.items():
        print(f"\n📋 {data_type.upper()} 테스트:")
        print("-" * 30)

        try:
            # 1. 포맷 감지
            if data_type == 'ticker':
                detected = detect_ticker_format(simple_data)
            elif data_type == 'trade':
                detected = detect_trade_format(simple_data)
            elif data_type == 'orderbook':
                detected = detect_orderbook_format(simple_data)
            elif data_type == 'candle':
                detected = detect_candle_format(simple_data)
            elif data_type == 'myorder':
                detected = detect_myorder_format(simple_data)

            print(f"🔍 감지된 포맷: {detected}")

            # 2. SIMPLE → DEFAULT 변환
            default_data = convert_from_simple_format(simple_data, data_type)
            print(f"✅ DEFAULT 변환: {default_data.get('type')} / {default_data.get('code')}")

            # 3. DEFAULT → SIMPLE 재변환 (라운드트립)
            simple_again = convert_to_simple_format(default_data, data_type)
            print(f"✅ SIMPLE 재변환: {simple_again.get('ty')} / {simple_again.get('cd')}")

            # 4. 자동 감지 변환
            auto_converted = auto_detect_and_convert(simple_data)
            print(f"✅ 자동 변환: {auto_converted.get('type')} 포맷으로 변환 완료")

        except Exception as e:
            print(f"❌ {data_type} 테스트 실패: {e}")

    print(f"\n🎯 통합 테스트 완료!")


# 테스트 실행 (개발 중에만)
if __name__ == "__main__":
    test_all_simple_conversions()
