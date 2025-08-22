# WebSocket 캐시 관리 전략 가이드

## 🎯 WebSocket vs REST API 본질적 차이

### WebSocket = 실시간 스트림 ONLY
- ✅ **최신 1개 정보만** 실시간 업데이트
- ❌ **과거 데이터/다중 데이터 불가능**

### REST API = 히스토리 조회 전용
- ✅ **과거 데이터 조회 가능** (count, to 매개변수)
- ❌ **실시간 스트림 불가능**

## 🚨 데이터 무결성 보장 규칙

### 1단계: WebSocket 제약 검증 (필수)
```python
# ✅ WebSocket 허용 조건
if request.data_type in [DataType.CANDLES, DataType.TRADES]:
    if request.to is not None:
        return REST_API  # 과거 데이터는 REST 필수
    if request.count and request.count > 1:
        return REST_API  # 다중 데이터는 REST 필수

# ✅ WebSocket vs REST 경합 (단일 최신 데이터만)
# - 단일 캔들/체결/티커/호가
```

### 2단계: 스마트 선택 (허용된 범위 내)
```python
# WebSocket 우선 조건
- 실시간성 요구 (RealtimePriority.HIGH)
- 다중 심볼 효율성
- 네트워크 안정성

# REST API 우선 조건
- 안정성 요구 (RealtimePriority.LOW)
- Rate Limit 상태
- 대용량 데이터
```

## 🔄 WebSocket 캐시 관리 전략

### 실시간 캐시 시스템
```python
class WebSocketCache:
    """WebSocket 실시간 데이터 캐시"""

    def __init__(self):
        self.ticker_cache = {}      # symbol -> latest_ticker
        self.candle_cache = {}      # (symbol, interval) -> latest_candle
        self.trade_cache = {}       # symbol -> latest_trade
        self.orderbook_cache = {}   # symbol -> latest_orderbook

    def update_ticker(self, symbol: str, data: dict):
        """티커 업데이트 (중복 제거)"""
        if symbol not in self.ticker_cache or \
           data['trade_timestamp'] > self.ticker_cache[symbol]['trade_timestamp']:
            self.ticker_cache[symbol] = data

    def update_candle(self, symbol: str, interval: str, data: dict):
        """캔들 업데이트 (중복 제거)"""
        key = (symbol, interval)
        if key not in self.candle_cache or \
           data['candle_date_time'] > self.candle_cache[key]['candle_date_time']:
            self.candle_cache[key] = data
```

### 중복 데이터 방지
```python
def prevent_duplicate_data(self, new_data: dict, cache_key: str) -> bool:
    """중복 데이터 방지 검증"""
    if cache_key not in self.cache:
        return True  # 새 데이터

    cached_data = self.cache[cache_key]

    # 타임스탬프 기반 중복 검사
    if 'timestamp' in new_data and 'timestamp' in cached_data:
        return new_data['timestamp'] > cached_data['timestamp']

    # 캔들 시간 기반 중복 검사
    if 'candle_date_time' in new_data:
        return new_data['candle_date_time'] != cached_data.get('candle_date_time')

    return True  # 기본적으로 허용
```

## 📋 실전 사용 가이드

### ✅ 올바른 사용법
```python
# 실시간 최신 데이터
latest_ticker = await smart_router.get_ticker(["KRW-BTC"])
latest_candle = await smart_router.get_candles(["KRW-BTC"], interval="5m", count=1)

# 과거/다중 데이터
historical_candles = await smart_router.get_candles(
    ["KRW-BTC"],
    interval="1h",
    count=24,
    to="2025-08-22T00:00:00Z"
)
```

### ❌ 위험한 사용법
```python
# WebSocket으로 다중 캔들 요청 (같은 데이터 중복 위험)
await smart_router.get_candles(["KRW-BTC"], interval="5m", count=10)  # 🚨 위험

# WebSocket으로 과거 데이터 요청 (불가능)
await smart_router.get_candles(
    ["KRW-BTC"],
    count=5,
    to="2025-08-21T00:00:00Z"
)  # 🚨 위험
```

## 🔧 캐시 최적화 전략

### 1. 메모리 관리
- **TTL 설정**: 1분 이상 된 데이터 자동 삭제
- **크기 제한**: 심볼당 최대 캐시 개수 제한
- **압축**: 불필요한 필드 제거

### 2. 일관성 보장
- **버전 관리**: 타임스탬프 기반 최신성 검증
- **중복 제거**: 동일 시간 데이터 필터링
- **순서 보장**: 시간순 정렬 유지

### 3. 성능 최적화
- **배치 업데이트**: 다중 심볼 일괄 처리
- **지연 로딩**: 필요시에만 캐시 로드
- **백그라운드 정리**: 주기적 캐시 정리

## 🎯 결론

**WebSocket 캐시 관리 핵심**:
1. **제약 인식**: WebSocket = 실시간 1개만
2. **중복 방지**: 타임스탬프 기반 검증
3. **성능 최적화**: 메모리/일관성 균형
4. **안전성 우선**: 의심스러우면 REST API 사용

이 전략을 통해 **데이터 무결성과 실시간성을 모두 확보**할 수 있습니다.
