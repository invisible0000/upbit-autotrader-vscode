# 🧠 Smart Routing 시스템 완전 가이드

## 🎯 **Smart Routing이란?**

Smart Routing은 **업비트 자동매매 시스템의 핵심 Layer 1**로, 모든 마켓 데이터 요청을 **거래소 독립적인 도메인 모델**로 추상화하여 제공하는 시스템입니다.

### 🔑 **핵심 가치**
- **완전한 추상화**: 내부 시스템이 업비트 API 구조를 전혀 몰라도 됨
- **자율적 최적화**: 내부 분석으로 REST ↔ WebSocket 자동 전환
- **실거래 성능**: 메모리 캐시 우선으로 밀리초 응답
- **3-Layer 기반**: Layer 1 역할에만 집중, 다른 Layer와 명확한 분리

## 🏗️ **시스템 아키텍처**

### 📊 **3-Layer 구조에서의 위치**
```
📱 클라이언트 (차트뷰어, 스크리너, 백테스터, 실거래봇)
    ↓
🌐 Layer 3: Market Data Storage (영속성, 캐싱)
    ↓
⚡ Layer 2: Market Data Coordinator (대용량 처리, 분할)
    ↓
🧠 Layer 1: Smart Routing (API 추상화, 채널 선택) ← 이 문서
    ↓
🔌 업비트 API (REST + WebSocket)
```

### 🎯 **Layer 1의 책임**
- **API 추상화**: URL 구조 완전 은닉
- **자율적 채널 선택**: REST vs WebSocket 내부 결정
- **업비트 제한 준수**: 200개 초과 시 명시적 에러
- **도메인 모델 제공**: TradingSymbol, Timeframe 등

## 🛠️ **핵심 구성요소**

### 📋 **1. 인터페이스 (Interfaces)**

#### IDataRouter - 메인 라우터 인터페이스
```python
class IDataRouter(ABC):
    """완전 추상화된 데이터 라우터"""

    async def get_candle_data(
        self,
        symbol: TradingSymbol,
        timeframe: Timeframe,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CandleDataResponse:
        """캔들 데이터 조회 (최대 200개)"""

    async def get_ticker_data(self, symbol: TradingSymbol) -> TickerDataResponse:
        """실시간 가격 정보"""

    async def get_orderbook_data(self, symbol: TradingSymbol) -> OrderbookDataResponse:
        """호가창 정보"""

    async def get_trade_data(self, symbol: TradingSymbol) -> TradeDataResponse:
        """체결 내역"""
```

#### IDataProvider - 거래소별 구현체 인터페이스
```python
class IDataProvider(ABC):
    """거래소별 데이터 제공자 (업비트 전용)"""

    async def fetch_candle_data(self, request: CandleDataRequest) -> CandleDataResponse:
        """실제 API 호출 로직"""
```

### 🎨 **2. 도메인 모델 (Models)**

#### TradingSymbol - 거래 심볼
```python
@dataclass(frozen=True)
class TradingSymbol:
    """거래소 독립적 심볼 표현"""
    base_currency: str      # BTC, ETH
    quote_currency: str     # KRW, USDT
    exchange: str = "upbit" # 거래소 식별

    @property
    def symbol(self) -> str:
        return f"{self.quote_currency}-{self.base_currency}"
```

#### Timeframe - 시간 프레임
```python
class Timeframe(Enum):
    """표준화된 타임프레임"""
    M1 = "1m"      # 1분봉
    M5 = "5m"      # 5분봉
    M15 = "15m"    # 15분봉
    H1 = "1h"      # 1시간봉
    D1 = "1d"      # 1일봉
```

#### 데이터 타입들
```python
@dataclass(frozen=True)
class CandleData:
    """OHLCV 캔들 데이터"""
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal

@dataclass(frozen=True)
class TickerData:
    """실시간 가격 정보"""
    timestamp: datetime
    current_price: Decimal
    change_rate: Decimal
    trade_volume_24h: Decimal
```

### 🚀 **3. 구현체 (Implementations)**

#### SmartDataRouter - 자율적 라우터
```python
class SmartDataRouter(IDataRouter):
    """자율적 채널 선택 라우터"""

    def __init__(self):
        self.rest_provider = UpbitRestProvider()
        self.websocket_provider = UpbitWebSocketProvider()
        self.frequency_analyzer = FrequencyAnalyzer()
        self.channel_selector = ChannelSelector()

        # 실시간 데이터 캐시 (새로 추가)
        self.realtime_cache = RealtimeDataCache()

    async def get_candle_data(self, symbol, timeframe, count=None, start_time=None, end_time=None):
        """하이브리드 캔들 데이터 제공"""

        # 1. API 제한 검증
        if self._estimate_count(start_time, end_time, timeframe) > 200:
            raise DataRangeExceedsLimitException("200개 초과, Coordinator 필요")

        # 2. 실시간 캐시 우선 확인
        cached_data = await self.realtime_cache.get_latest_candles(symbol, timeframe, count)
        if cached_data:
            return cached_data

        # 3. 자율적 채널 선택
        use_websocket = self.channel_selector.should_use_websocket(
            symbol, timeframe, self.frequency_analyzer.get_patterns()
        )

        if use_websocket:
            return await self.websocket_provider.get_candle_data(request)
        else:
            return await self.rest_provider.get_candle_data(request)
```

#### UpbitRestProvider - REST API 구현
```python
class UpbitRestProvider(IDataProvider):
    """업비트 REST API 제공자"""

    async def fetch_candle_data(self, request: CandleDataRequest):
        """업비트 REST API 호출"""
        # URL 구성은 여기서만 발생 (완전 은닉)
        url = f"/v1/candles/minutes/{request.timeframe.value}"
        params = {
            "market": request.symbol.symbol,
            "count": request.count
        }
        # ... 실제 API 호출
```

### 🔄 **4. 전략 (Strategies)**

#### FrequencyAnalyzer - 요청 패턴 분석
```python
class FrequencyAnalyzer:
    """요청 빈도 분석기"""

    def analyze_request_pattern(self, symbol: TradingSymbol, timeframe: Timeframe):
        """요청 패턴 분석하여 WebSocket 전환 권장"""
        frequency = self.get_request_frequency(symbol, timeframe)

        # 1분에 3회 이상 → WebSocket 권장
        if frequency > 3:
            return ChannelRecommendation.WEBSOCKET
        else:
            return ChannelRecommendation.REST
```

#### ChannelSelector - 채널 선택 전략
```python
class ChannelSelector:
    """자율적 채널 선택"""

    def should_use_websocket(self, symbol, timeframe, patterns):
        """WebSocket 사용 여부 결정"""

        # 실거래 중요 심볼 → WebSocket 우선
        if self.is_trading_symbol(symbol):
            return True

        # 고빈도 요청 → WebSocket
        if patterns.get_frequency(symbol, timeframe) > 3:
            return True

        # 기본값 → REST
        return False
```

## 💾 **실시간 데이터 아키텍처**

### 🔄 **하이브리드 데이터 흐름**
```
실거래 시나리오:
WebSocket 수신 → RealtimeDataCache (메모리) → 매매변수 계산기 (즉시)
                              ↓
                    캔들 완성 시 → CandleDB (비동기)

데이터 조회 시:
1. RealtimeDataCache 확인 (최신 미완성 캔들)
2. CandleDB 조회 (과거 완성된 캔들)
3. 통합하여 반환
```

### 📊 **RealtimeDataCache 설계**
```python
class RealtimeDataCache:
    """실거래 전용 메모리 캐시"""

    def __init__(self):
        # 심볼별 × 타임프레임별 슬라이딩 윈도우
        self._cache: Dict[str, Dict[str, CircularBuffer]] = {}

    async def update_realtime_point(self, symbol: str, price: Decimal, timestamp: datetime):
        """WebSocket에서 실시간 포인트 업데이트"""
        # 메모리에만 저장, DB 접근 없음

    async def get_latest_candles(self, symbol: str, timeframe: str, count: int):
        """매매변수 계산용 최신 데이터"""
        # 메모리 캐시에서 즉시 반환 (< 1ms)

    async def finalize_completed_candle(self, symbol: str, timeframe: str, candle: CandleData):
        """완성된 캔들을 DB에 저장하고 메모리 정리"""
        # Layer 3 Storage에 비동기 저장 요청
```

## 🎯 **API 제한 처리**

### 📏 **업비트 API 제한 준수**
```python
def validate_api_limits(start_time, end_time, count, timeframe):
    """API 제한 검증 (Smart Routing 책임)"""

    if start_time and end_time:
        estimated_count = calculate_candle_count(start_time, end_time, timeframe)
        if estimated_count > 200:
            raise DataRangeExceedsLimitException(
                f"요청 범위 초과: 예상 {estimated_count}개 > 최대 200개"
                f"Market Data Coordinator에서 분할 처리 필요"
            )

    if count and count > 200:
        raise InvalidRequestException("count는 최대 200개까지만 지원")
```

### 🔄 **Layer 간 역할 분리**
- **Smart Routing (Layer 1)**: 200개 이내만 처리, 초과 시 에러
- **Coordinator (Layer 2)**: 대용량 요청을 200개씩 분할하여 Layer 1 호출
- **Storage (Layer 3)**: 분할된 결과를 통합하여 최종 제공

## 🚀 **성능 최적화**

### ⚡ **실거래 성능 목표**
- **실시간 데이터 접근**: < 1ms (메모리 캐시)
- **캔들 데이터 조회**: < 10ms (캐시 + 빠른 DB)
- **WebSocket 처리**: < 5ms (비동기)
- **채널 전환 결정**: < 1ms (패턴 분석)

### 📊 **메모리 사용 최적화**
```python
# 슬라이딩 윈도우로 메모리 제한
_cache[symbol][timeframe] = CircularBuffer(max_size=500)  # 최대 500개 포인트

# TTL 기반 자동 정리
실시간 데이터: 5분 TTL
호가창 데이터: 30초 TTL
체결 데이터: 10분 TTL
```

## 🔧 **사용법 예시**

### 📱 **클라이언트에서의 사용**
```python
# 1. 라우터 초기화
router = SmartDataRouter()

# 2. 도메인 모델로 요청
symbol = TradingSymbol("BTC", "KRW")
timeframe = Timeframe.M1

# 3. 캔들 데이터 조회 (자동 최적화)
candles = await router.get_candle_data(symbol, timeframe, count=100)

# 4. 실시간 가격 조회
ticker = await router.get_ticker_data(symbol)
```

### 🎯 **실거래 시나리오**
```python
# 실거래봇의 사용법
async def trading_strategy():
    # 1분봉 400개 + 실시간값 조회
    historical = await router.get_candle_data(symbol, Timeframe.M1, count=400)
    realtime = await router.get_ticker_data(symbol)

    # 매매 신호 계산 (메모리 캐시로 밀리초 응답)
    signal = calculate_signal(historical, realtime)

    if signal == BUY:
        await execute_buy_order()
```

### 📊 **차트뷰어 시나리오**
```python
# 차트뷰어의 사용법
async def update_chart():
    # 1200개 캔들 요청 → Layer 2 Coordinator가 분할 처리
    candles = await coordinator.get_candle_data(symbol, timeframe, count=1200)

    # 실시간 업데이트
    ticker = await router.get_ticker_data(symbol)

    # 차트 렌더링
    render_candlestick_chart(candles + [ticker])
```

## 🎯 **핵심 설계 원칙**

### ✅ **DO (해야 할 것)**
- 도메인 모델만 사용 (TradingSymbol, Timeframe)
- 200개 이내 요청만 처리
- 실시간 캐시 우선 조회
- 자율적 채널 선택
- 완전한 API 추상화

### ❌ **DON'T (하지 말 것)**
- URL 구조 노출 금지
- 200개 초과 처리 금지 (Coordinator 역할)
- DB 직접 접근 금지 (Storage 역할)
- 대용량 분할 처리 금지 (Coordinator 역할)
- UI 로직 포함 금지 (Presentation 역할)

## 🔄 **다른 Layer와의 협력**

### 📊 **Layer 2 (Coordinator)와의 관계**
```python
# Coordinator가 Smart Routing 사용
async def get_large_dataset():
    chunks = split_request_into_200s()

    results = []
    for chunk in chunks:
        # Layer 1에 200개씩 요청
        data = await smart_router.get_candle_data(chunk)
        results.append(data)

    return merge_results(results)
```

### 💾 **Layer 3 (Storage)와의 관계**
```python
# Smart Router → Storage 캔들 완성 알림
async def on_candle_completed(symbol, timeframe, candle):
    # Storage Layer에 비동기 저장 요청
    await storage.store_completed_candle(symbol, timeframe, candle)

    # 메모리 캐시 정리
    self.realtime_cache.cleanup_completed(symbol, timeframe)
```

---

## 📚 **관련 문서**
- [Market Data Coordinator 가이드](../coordinator/README.md)
- [Market Data Storage 가이드](../storage/README.md)
- [3-Layer 아키텍처 개요](../README.md)
- [실시간 데이터 아키텍처](../../REALTIME_DATA_ARCHITECTURE_PLAN.md)
