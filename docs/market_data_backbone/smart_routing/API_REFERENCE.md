# Smart Routing API 참조

## 📖 **캔들 데이터 API 개선**

### 🎯 **스냅샷/실시간 구분 지원**

```python
# 실시간 캔들만 요청 (현재 진행 중인 캔들)
realtime_candles = await router.get_candle_data(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.MINUTE_1,
    realtime_only=True  # stream_type: REALTIME만
)

# 스냅샷 캔들만 요청 (완성된 과거 캔들)
historical_candles = await router.get_candle_data(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.MINUTE_1,
    count=200,
    snapshot_only=True  # stream_type: SNAPSHOT만
)

# 하이브리드 요청 (스냅샷 + 실시간, 기본값)
hybrid_candles = await router.get_candle_data(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.MINUTE_1,
    count=200
    # realtime_only=False, snapshot_only=False
)
```

### 🎨 **RequestFactory 새로운 팩토리 메서드**

```python
# 실시간 트레이딩용 (현재 캔들만)
request = RequestFactory.realtime_candles(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.MINUTE_1
)

# 백테스팅용 (과거 완성된 캔들만)
request = RequestFactory.historical_candles(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.HOUR_1,
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2025, 1, 31)
)

# 하이브리드 분석용 (스냅샷 + 실시간)
request = RequestFactory.hybrid_candles(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.MINUTE_5,
    count=100
)
```

## 🔗 **구독 묶음 관리 시스템**

### 🎯 **기능별 구독 묶음**

```python
from ..strategies.subscription_bundling import (
    SubscriptionManager,
    SubscriptionPurpose
)

manager = SubscriptionManager()

# 1. 실시간 트레이딩 묶음
trading_bundle = manager.strategy.create_trading_bundle(
    symbols=[TradingSymbol("KRW-BTC"), TradingSymbol("KRW-ETH")],
    timeframes=["candle.1m", "candle.5m"]
)
# → ticker + orderbook + candle.1m + candle.5m

# 2. 포트폴리오 모니터링 묶음
monitoring_bundle = manager.strategy.create_monitoring_bundle(
    symbols=[TradingSymbol("KRW-BTC"), TradingSymbol("KRW-ETH"), TradingSymbol("KRW-ADA")]
)
# → ticker만 (여러 심볼)

# 3. 차트 분석 묶음
analysis_bundle = manager.strategy.create_analysis_bundle(
    symbol=TradingSymbol("KRW-BTC"),
    timeframes=["candle.1m", "candle.15m", "candle.1h"]
)
# → ticker + 여러 timeframe 캔들

# 4. 급변 감지 묶음
alert_bundle = manager.strategy.create_alert_bundle(
    symbols=[TradingSymbol("KRW-BTC"), TradingSymbol("KRW-ETH")]
)
# → ticker + trade (빠른 감지)
```

### � **구독 우선순위 시스템**

```python
# Smart Router에서 목적별 구독
subscription_id = await router.subscribe_realtime(
    symbol=TradingSymbol("KRW-BTC"),
    data_types=["ticker", "orderbook"],
    callback=handle_trading_data,
    purpose="trading"  # 우선순위 1 (최고)
)

# 구독 목적별 우선순위
# trading: 1 (최고)
# alert: 2 (높음)
# monitoring: 3 (중간)
# analysis: 4 (중간)
# backtesting: 5 (낮음)
```

### 🌐 **업비트 WebSocket 요청 최적화**

```python
# 구독 묶음이 생성하는 WebSocket 요청 예시
trading_request = trading_bundle.get_websocket_request("trading_001")

# 결과:
[
    {"ticket": "trading_001"},
    {
        "type": "ticker",
        "codes": ["KRW-BTC", "KRW-ETH"]
    },
    {
        "type": "orderbook",
        "codes": ["KRW-BTC", "KRW-ETH"]
    },
    {
        "type": "candle.1m",
        "codes": ["KRW-BTC", "KRW-ETH"]
    },
    {
        "type": "candle.5m",
        "codes": ["KRW-BTC", "KRW-ETH"]
    },
    {"format": "DEFAULT"}
]
```

## 🧠 **업비트 API 스냅샷/실시간 구분 이해**

### 📋 **업비트 WebSocket 캔들 동작 방식**

1. **최초 구독**: 과거 완성된 캔들 전송 (`stream_type: "SNAPSHOT"`)
2. **실시간 업데이트**: 체결 발생 시 현재 캔들 업데이트 (`stream_type: "REALTIME"`)
3. **중복 전송**: 같은 `candle_date_time`이 여러 번 올 수 있음 (최신 데이터가 정확)

### 🎯 **Smart Router 대응 전략**

| 요청 타입 | 사용 시나리오 | WebSocket 옵션 |
|-----------|---------------|----------------|
| `realtime_only=True` | 실시간 트레이딩, 현재 캔들 추적 | `is_only_realtime: true` |
| `snapshot_only=True` | 백테스팅, 과거 데이터 분석 | `is_only_snapshot: true` |
| 기본값 (둘 다 False) | 차트 표시, 하이브리드 분석 | 둘 다 수신 |

### 🔄 **구독 묶음 성질별 분류**

| 묶음 성질 | 데이터 조합 | 최적 시나리오 |
|-----------|-------------|---------------|
| **가격 기반** | ticker + candle | 일반적인 시세 추적 |
| **깊이 기반** | orderbook | 호가창 분석, 대량 거래 |
| **체결 기반** | trade + ticker | 급변 감지, 거래량 분석 |
| **올인원** | ticker + orderbook + trade + candle | 실시간 트레이딩 |

## 🚀 **실제 사용 시나리오**

### 💰 **실시간 트레이딩 시스템**

```python
# 1. 실시간 가격 추적
async def setup_trading_subscriptions():
    # 현재 진행 중인 1분봉 실시간 추적
    current_candle = await router.get_candle_data(
        symbol=TradingSymbol("KRW-BTC"),
        timeframe=Timeframe.MINUTE_1,
        realtime_only=True
    )

    # 실시간 구독 (트레이딩 최우선)
    subscription = await router.subscribe_realtime(
        symbol=TradingSymbol("KRW-BTC"),
        data_types=["ticker", "orderbook", "candle.1m"],
        callback=handle_trading_update,
        purpose="trading"  # 우선순위 1
    )
```

### 📊 **백테스팅 시스템**

```python
# 2. 과거 데이터 전용 분석
async def setup_backtesting():
    # 완성된 과거 캔들만 요청
    historical_data = await router.get_candle_data(
        symbol=TradingSymbol("KRW-BTC"),
        timeframe=Timeframe.HOUR_1,
        start_time=datetime(2024, 1, 1),
        end_time=datetime(2024, 12, 31),
        snapshot_only=True  # 실시간 업데이트 불필요
    )
```

### 🔍 **포트폴리오 모니터링**

```python
# 3. 다종목 모니터링
async def setup_portfolio_monitoring():
    symbols = [
        TradingSymbol("KRW-BTC"),
        TradingSymbol("KRW-ETH"),
        TradingSymbol("KRW-ADA")
    ]

    # 모니터링 전용 구독 묶음
    for symbol in symbols:
        await router.subscribe_realtime(
            symbol=symbol,
            data_types=["ticker"],  # 티커만으로 충분
            callback=handle_portfolio_update,
            purpose="monitoring"  # 우선순위 3
        )
```

### ⚡ **급변 감지 시스템**

```python
# 4. 급등/급락 감지
async def setup_volatility_detection():
    await router.subscribe_realtime(
        symbol=TradingSymbol("KRW-BTC"),
        data_types=["ticker", "trade"],  # 빠른 감지용
        callback=handle_volatility_alert,
        purpose="alert"  # 우선순위 2
    )
```

## 📈 **성능 최적화 권장사항**

### 🎯 **구독 전략**

1. **목적별 분리**: 트레이딩/모니터링/분석을 별도 구독으로 관리
2. **우선순위 설정**: 중요한 기능에 높은 우선순위 부여
3. **묶음 최적화**: 동일한 심볼+데이터타입은 하나의 구독으로 통합
4. **필요한 것만**: 불필요한 데이터 타입은 구독하지 않음

### ⚡ **레이턴시 최적화**

```python
# 고빈도 트레이딩: WebSocket 우선
high_freq_data = await router.get_ticker_data(
    symbol=TradingSymbol("KRW-BTC")
)
# → 자동으로 WebSocket 사용 (빈도 분석 기반)

# 일회성 조회: REST API 효율적
one_time_data = await router.get_candle_data(
    symbol=TradingSymbol("KRW-BTC"),
    timeframe=Timeframe.DAY_1,
    count=30,
    snapshot_only=True
)
# → REST API 사용 권장
```

이 개선된 Smart Router는 업비트 WebSocket의 유연한 구독 시스템을 완전히 활용하여 효율적이고 목적별로 최적화된 데이터 수신을 제공합니다.

## 📋 **인터페이스 상세**

### IDataRouter - 메인 라우터 인터페이스

#### get_candle_data()
```python
async def get_candle_data(
    self,
    symbol: TradingSymbol,
    timeframe: Timeframe,
    count: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> CandleDataResponse:
```

**매개변수:**
- `symbol`: 거래 심볼 (예: TradingSymbol("BTC", "KRW"))
- `timeframe`: 시간 프레임 (예: Timeframe.M1)
- `count`: 요청할 캔들 수 (최대 200개)
- `start_time`: 시작 시간 (선택적)
- `end_time`: 종료 시간 (선택적)

**반환값:**
- `CandleDataResponse`: 캔들 데이터 리스트

**예외:**
- `DataRangeExceedsLimitException`: 200개 초과 요청 시
- `InvalidRequestException`: 잘못된 매개변수
- `SymbolNotSupportedException`: 지원하지 않는 심볼

**사용 예시:**
```python
# 최근 100개 1분봉
candles = await router.get_candle_data(
    TradingSymbol("BTC", "KRW"),
    Timeframe.M1,
    count=100
)

# 특정 기간 조회
candles = await router.get_candle_data(
    TradingSymbol("ETH", "KRW"),
    Timeframe.H1,
    start_time=datetime(2025, 8, 1),
    end_time=datetime(2025, 8, 20)
)
```

#### get_ticker_data()
```python
async def get_ticker_data(self, symbol: TradingSymbol) -> TickerDataResponse:
```

**매개변수:**
- `symbol`: 거래 심볼

**반환값:**
- `TickerDataResponse`: 실시간 가격 정보

**사용 예시:**
```python
ticker = await router.get_ticker_data(TradingSymbol("BTC", "KRW"))
print(f"현재가: {ticker.current_price:,}원")
print(f"변동률: {ticker.change_rate:.2f}%")
```

#### get_orderbook_data()
```python
async def get_orderbook_data(self, symbol: TradingSymbol) -> OrderbookDataResponse:
```

**매개변수:**
- `symbol`: 거래 심볼

**반환값:**
- `OrderbookDataResponse`: 호가창 정보

**사용 예시:**
```python
orderbook = await router.get_orderbook_data(TradingSymbol("BTC", "KRW"))
print(f"최우선 매수호가: {orderbook.best_bid_price:,}원")
print(f"최우선 매도호가: {orderbook.best_ask_price:,}원")
```

#### get_trade_data()
```python
async def get_trade_data(self, symbol: TradingSymbol) -> TradeDataResponse:
```

**매개변수:**
- `symbol`: 거래 심볼

**반환값:**
- `TradeDataResponse`: 최근 체결 내역

#### subscribe_realtime()
```python
async def subscribe_realtime(
    self,
    symbol: TradingSymbol,
    data_types: List[DataType],
    callback: Callable[[RealtimeData], None]
) -> str:
```

**매개변수:**
- `symbol`: 구독할 심볼
- `data_types`: 구독할 데이터 타입 리스트
- `callback`: 데이터 수신 시 호출할 콜백 함수

**반환값:**
- `str`: 구독 ID

**사용 예시:**
```python
def on_ticker_update(data):
    print(f"실시간 가격: {data.current_price:,}원")

subscription_id = await router.subscribe_realtime(
    TradingSymbol("BTC", "KRW"),
    [DataType.TICKER],
    on_ticker_update
)
```

#### unsubscribe_realtime()
```python
async def unsubscribe_realtime(self, subscription_id: str) -> bool:
```

**매개변수:**
- `subscription_id`: 구독 ID

**반환값:**
- `bool`: 구독 해제 성공 여부

#### get_routing_stats()
```python
async def get_routing_stats(self) -> RoutingStatsResponse:
```

**반환값:**
- `RoutingStatsResponse`: 라우팅 통계 정보

**사용 예시:**
```python
stats = await router.get_routing_stats()
print(f"전체 요청 수: {stats.total_requests}")
print(f"WebSocket 사용률: {stats.websocket_ratio:.1%}")
```

## 🎨 **도메인 모델 상세**

### TradingSymbol
```python
@dataclass(frozen=True)
class TradingSymbol:
    base_currency: str      # 기본 통화 (BTC, ETH, etc.)
    quote_currency: str     # 견적 통화 (KRW, USDT, etc.)
    exchange: str = "upbit" # 거래소 식별자

    @property
    def symbol(self) -> str:
        """업비트 형식 심볼 반환 (KRW-BTC)"""
        return f"{self.quote_currency}-{self.base_currency}"

    @classmethod
    def from_upbit_symbol(cls, symbol: str) -> "TradingSymbol":
        """업비트 심볼에서 생성 (KRW-BTC → TradingSymbol)"""
        quote, base = symbol.split('-')
        return cls(base, quote)
```

**사용 예시:**
```python
# 직접 생성
btc = TradingSymbol("BTC", "KRW")

# 업비트 심볼에서 생성
eth = TradingSymbol.from_upbit_symbol("KRW-ETH")

# 심볼 문자열 얻기
print(btc.symbol)  # "KRW-BTC"
```

### Timeframe
```python
class Timeframe(Enum):
    M1 = "1m"      # 1분봉
    M3 = "3m"      # 3분봉
    M5 = "5m"      # 5분봉
    M15 = "15m"    # 15분봉
    M30 = "30m"    # 30분봉
    H1 = "1h"      # 1시간봉
    H4 = "4h"      # 4시간봉
    D1 = "1d"      # 1일봉
    W1 = "1w"      # 1주봉
    MON1 = "1M"    # 1개월봉

    @property
    def minutes(self) -> int:
        """타임프레임을 분 단위로 변환"""
        mapping = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440, "1w": 10080, "1M": 43200
        }
        return mapping[self.value]
```

### CandleData
```python
@dataclass(frozen=True)
class CandleData:
    timestamp: datetime      # 캔들 시작 시간
    open_price: Decimal     # 시가
    high_price: Decimal     # 고가
    low_price: Decimal      # 저가
    close_price: Decimal    # 종가
    volume: Decimal         # 거래량
    quote_volume: Optional[Decimal] = None  # 견적 통화 거래량

    @property
    def ohlc(self) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """OHLC 튜플 반환"""
        return (self.open_price, self.high_price, self.low_price, self.close_price)

    @property
    def price_change(self) -> Decimal:
        """가격 변화 (종가 - 시가)"""
        return self.close_price - self.open_price

    @property
    def price_change_rate(self) -> Decimal:
        """가격 변화율 (%)"""
        if self.open_price == 0:
            return Decimal('0')
        return (self.close_price - self.open_price) / self.open_price * 100
```

### TickerData
```python
@dataclass(frozen=True)
class TickerData:
    timestamp: datetime          # 시간
    current_price: Decimal      # 현재가
    change_rate: Decimal        # 변동률 (%)
    change_amount: Decimal      # 변동 금액
    trade_volume_24h: Decimal   # 24시간 거래량
    trade_value_24h: Decimal    # 24시간 거래대금
    high_price_24h: Decimal     # 24시간 고가
    low_price_24h: Decimal      # 24시간 저가
    opening_price: Decimal      # 당일 시가
```

### OrderbookData
```python
@dataclass(frozen=True)
class OrderbookUnit:
    bid_price: Decimal      # 매수 호가
    bid_size: Decimal       # 매수 잔량
    ask_price: Decimal      # 매도 호가
    ask_size: Decimal       # 매도 잔량

@dataclass(frozen=True)
class OrderbookData:
    timestamp: datetime              # 시간
    units: List[OrderbookUnit]       # 호가 리스트 (30개)

    @property
    def best_bid_price(self) -> Decimal:
        """최우선 매수호가"""
        return self.units[0].bid_price if self.units else Decimal('0')

    @property
    def best_ask_price(self) -> Decimal:
        """최우선 매도호가"""
        return self.units[0].ask_price if self.units else Decimal('0')
```

### TradeData
```python
@dataclass(frozen=True)
class TradeData:
    timestamp: datetime      # 체결 시간
    price: Decimal          # 체결 가격
    volume: Decimal         # 체결 수량
    side: str              # 체결 종류 (BID/ASK)
    sequential_id: int     # 체결 번호
```

## 📊 **응답 모델**

### CandleDataResponse
```python
@dataclass(frozen=True)
class CandleDataResponse:
    candles: List[CandleData]    # 캔들 데이터 리스트
    symbol: TradingSymbol        # 요청 심볼
    timeframe: Timeframe         # 요청 타임프레임
    count: int                   # 실제 반환된 개수

    @property
    def latest_candle(self) -> Optional[CandleData]:
        """가장 최근 캔들"""
        return self.candles[-1] if self.candles else None
```

### TickerDataResponse
```python
@dataclass(frozen=True)
class TickerDataResponse:
    ticker: TickerData       # 티커 데이터
    symbol: TradingSymbol    # 심볼
    source: str              # 데이터 소스 (cache/websocket/rest)
```

### OrderbookDataResponse
```python
@dataclass(frozen=True)
class OrderbookDataResponse:
    orderbook: OrderbookData # 호가창 데이터
    symbol: TradingSymbol    # 심볼
    depth: int               # 호가 깊이
```

### TradeDataResponse
```python
@dataclass(frozen=True)
class TradeDataResponse:
    trades: List[TradeData]  # 체결 내역 리스트
    symbol: TradingSymbol    # 심볼
    count: int               # 체결 건수
```

### RoutingStatsResponse
```python
@dataclass(frozen=True)
class RoutingStatsResponse:
    total_requests: int              # 전체 요청 수
    websocket_requests: int          # WebSocket 요청 수
    rest_requests: int               # REST 요청 수
    error_count: int                 # 에러 발생 수
    avg_response_time_ms: float      # 평균 응답 시간 (ms)
    cache_hit_ratio: float           # 캐시 히트율
    active_subscriptions: int        # 활성 구독 수

    @property
    def websocket_ratio(self) -> float:
        """WebSocket 사용률"""
        if self.total_requests == 0:
            return 0.0
        return self.websocket_requests / self.total_requests
```

## ⚠️ **예외 처리**

### 주요 예외 클래스
```python
class SmartRoutingException(Exception):
    """Smart Routing 기본 예외"""
    pass

class DataRangeExceedsLimitException(SmartRoutingException):
    """API 제한 초과 예외 (200개 초과)"""
    pass

class InvalidRequestException(SmartRoutingException):
    """잘못된 요청 예외"""
    pass

class SymbolNotSupportedException(SmartRoutingException):
    """지원하지 않는 심볼 예외"""
    pass

class TimeframeNotSupportedException(SmartRoutingException):
    """지원하지 않는 타임프레임 예외"""
    pass

class ApiRateLimitException(SmartRoutingException):
    """API 레이트 제한 예외"""
    pass

class WebSocketConnectionException(SmartRoutingException):
    """WebSocket 연결 예외"""
    pass
```

### 예외 처리 예시
```python
try:
    candles = await router.get_candle_data(symbol, timeframe, count=500)
except DataRangeExceedsLimitException as e:
    # Coordinator를 통한 분할 처리 필요
    candles = await coordinator.get_candle_data(symbol, timeframe, count=500)
except SymbolNotSupportedException as e:
    logger.error(f"지원하지 않는 심볼: {symbol}")
except ApiRateLimitException as e:
    # 잠시 대기 후 재시도
    await asyncio.sleep(1)
    candles = await router.get_candle_data(symbol, timeframe, count=100)
```

## 🔧 **설정 및 초기화**

### SmartDataRouter 초기화
```python
# 기본 초기화
router = SmartDataRouter()

# 커스텀 설정
router = SmartDataRouter(
    rest_provider=UpbitRestProvider(api_key="your_key"),
    websocket_provider=UpbitWebSocketProvider(),
    channel_selector=AdvancedChannelSelector(),
    frequency_analyzer=MLFrequencyAnalyzer()
)
```

### 환경 변수 설정
```bash
# API 키 설정
export UPBIT_ACCESS_KEY="your_access_key"
export UPBIT_SECRET_KEY="your_secret_key"

# 로깅 설정
export UPBIT_LOG_LEVEL="INFO"
export UPBIT_LOG_SCOPE="verbose"

# 성능 설정
export SMART_ROUTING_CACHE_SIZE="1000"
export SMART_ROUTING_WEBSOCKET_TIMEOUT="10"
```

## 📈 **성능 모니터링**

### 라우팅 통계 확인
```python
# 주기적 통계 확인
async def monitor_routing_performance():
    while True:
        stats = await router.get_routing_stats()

        print(f"WebSocket 사용률: {stats.websocket_ratio:.1%}")
        print(f"평균 응답시간: {stats.avg_response_time_ms:.1f}ms")
        print(f"캐시 히트율: {stats.cache_hit_ratio:.1%}")

        if stats.avg_response_time_ms > 100:
            logger.warning("응답 시간이 100ms를 초과했습니다")

        await asyncio.sleep(60)  # 1분마다 확인
```

### 헬스 체크
```python
health = await router.health_check()
if health.status == "healthy":
    print("Smart Router 정상 동작 중")
else:
    print(f"문제 발생: {health.issues}")
```
