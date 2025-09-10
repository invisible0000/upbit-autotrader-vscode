# 📋 CandleDataProvider v5.0 - API Documentation & Usage Examples
> 완전한 API 명세서 및 실제 사용 예시

## 🎯 API Overview

### Single Entry Point
```python
class CandleDataProvider:
    """캔들 데이터 Infrastructure Service - 서브시스템들의 단일 진입점"""

    async def get_candles(
        symbol: str,                    # 거래 심볼
        timeframe: str,                 # 타임프레임
        count: Optional[int] = None,    # 캔들 개수
        start_time: Optional[datetime] = None,  # 시작 시간
        end_time: Optional[datetime] = None,    # 종료 시간
        inclusive_start: bool = True    # start_time 포함 여부
    ) -> CandleDataResponse
```

### 지원 파라미터 조합 (5가지)
1. **`count만`**: 최신 데이터부터 역순
2. **`start_time + count`**: 특정 시점부터 개수 지정
3. **`start_time + end_time`**: 구간 지정
4. **`count + end_time`**: 종료점까지 역순
5. **`모든 파라미터`**: 범위 내에서 최대 개수

---

## 📋 Detailed API Specification

### Main Method: `get_candles()`

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `symbol` | `str` | ✅ | - | 거래 심볼 (예: 'KRW-BTC', 'KRW-ETH') |
| `timeframe` | `str` | ✅ | - | 타임프레임 ('1s'~'1y', 27개 지원) |
| `count` | `Optional[int]` | ⚪ | `None` | 캔들 개수 (1~10000) |
| `start_time` | `Optional[datetime]` | ⚪ | `None` | 시작 시간 (UTC timezone) |
| `end_time` | `Optional[datetime]` | ⚪ | `None` | 종료 시간 (UTC timezone) |
| `inclusive_start` | `bool` | ⚪ | `True` | start_time 포함 여부 |

#### Supported Timeframes (27개)
```python
TIMEFRAMES = [
    # 초봉
    '1s',

    # 분봉
    '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m',

    # 시간봉 (분봉과 중복, 호환성)
    '1h',    # = 60m
    '4h',    # = 240m

    # 일/주/월/년봉
    '1d', '1w', '1M', '1y'
]
```

#### Parameter Validation Rules

1. **최소 요구사항**: `count`, `start_time+count`, `start_time+end_time` 중 하나는 필수
2. **count 범위**: 1 ≤ count ≤ 10000
3. **시간 순서**: start_time < end_time (제공시)
4. **미래 시간**: 현재 시간보다 미래인 요청은 `ValidationError`
5. **타임프레임**: 지원하지 않는 타임프레임은 `ValidationError`

#### Return Type: `CandleDataResponse`

```python
@dataclass
class CandleDataResponse:
    success: bool                    # 성공 여부
    candles: List[CandleData]       # 캔들 데이터 리스트 (시간순 정렬)
    total_count: int                # 실제 반환된 캔들 수
    data_source: str                # 데이터 소스 ("cache"/"db"/"api"/"mixed")
    response_time_ms: float         # 응답 시간 (밀리초)
    error_message: Optional[str]    # 에러 메시지 (실패시만)
```

#### CandleData Model

```python
@dataclass
class CandleData:
    # === 업비트 API 기본 필드 ===
    market: str                     # 페어 코드 (KRW-BTC)
    candle_date_time_utc: str      # UTC 시간 문자열
    candle_date_time_kst: str      # KST 시간 문자열
    opening_price: float           # 시가
    high_price: float             # 고가
    low_price: float              # 저가
    trade_price: float            # 종가
    timestamp: int                # 마지막 틱 타임스탬프 (ms)
    candle_acc_trade_price: float # 누적 거래 금액
    candle_acc_trade_volume: float # 누적 거래량

    # === 타임프레임별 고유 필드 (Optional) ===
    unit: Optional[int]                    # 초봉/분봉: 캔들 단위
    prev_closing_price: Optional[float]    # 일봉: 전일 종가
    change_price: Optional[float]          # 일봉: 가격 변화
    change_rate: Optional[float]           # 일봉: 변화율
    first_day_of_period: Optional[str]     # 주봉~연봉: 집계 시작일
    converted_trade_price: Optional[float] # 일봉: 환산 종가

    # === 편의성 필드 ===
    symbol: str                    # market에서 추출
    timeframe: str                 # 별도 지정
```

---

## 🔧 Usage Examples

### Example 1: 최신 캔들 조회 (count만)

```python
from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient

# 초기화
db_manager = DatabaseManager()
upbit_client = UpbitPublicClient()
provider = CandleDataProvider(db_manager, upbit_client)

# 최신 100개 5분봉 조회
response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="5m",
    count=100
)

print(f"성공: {response.success}")
print(f"캔들 수: {response.total_count}")
print(f"데이터 소스: {response.data_source}")
print(f"응답 시간: {response.response_time_ms:.2f}ms")

# 최신 캔들 (첫 번째)
latest_candle = response.candles[0]
print(f"최신 가격: {latest_candle.trade_price:,.0f}원")
print(f"거래량: {latest_candle.candle_acc_trade_volume:.2f} BTC")
```

**예상 출력**:
```
성공: True
캔들 수: 100
데이터 소스: mixed
응답 시간: 45.23ms
최신 가격: 95,200,000원
거래량: 12.34 BTC
```

### Example 2: 특정 시점부터 조회 (start_time + count)

```python
from datetime import datetime, timezone

# 2024년 1월 1일부터 1000개 일봉 조회
start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

response = await provider.get_candles(
    symbol="KRW-ETH",
    timeframe="1d",
    start_time=start_time,
    count=1000,
    inclusive_start=True  # start_time 포함
)

print(f"조회 기간: {response.candles[0].candle_date_time_utc} ~ {response.candles[-1].candle_date_time_utc}")
print(f"실제 캔들 수: {len(response.candles)}개")

# 첫날과 마지막날 가격 비교
first_candle = response.candles[0]
last_candle = response.candles[-1]
price_change = ((last_candle.trade_price - first_candle.trade_price) / first_candle.trade_price) * 100

print(f"첫날 종가: {first_candle.trade_price:,.0f}원")
print(f"마지막날 종가: {last_candle.trade_price:,.0f}원")
print(f"수익률: {price_change:+.2f}%")
```

**예상 출력**:
```
조회 기간: 2024-01-01T00:00:00Z ~ 2024-09-27T00:00:00Z
실제 캔들 수: 271개
첫날 종가: 2,890,000원
마지막날 종가: 4,120,000원
수익률: +42.56%
```

### Example 3: 구간 지정 조회 (start_time + end_time)

```python
# 2024년 8월 한달간 1시간봉 조회
start_time = datetime(2024, 8, 1, tzinfo=timezone.utc)
end_time = datetime(2024, 8, 31, 23, 59, 59, tzinfo=timezone.utc)

response = await provider.get_candles(
    symbol="KRW-BTC",
    timeframe="1h",
    start_time=start_time,
    end_time=end_time
)

print(f"8월 총 시간봉: {response.total_count}개")
print(f"데이터 소스: {response.data_source}")

# 8월 중 최고가/최저가 찾기
max_price = max(candle.high_price for candle in response.candles)
min_price = min(candle.low_price for candle in response.candles)
volatility = ((max_price - min_price) / min_price) * 100

print(f"8월 최고가: {max_price:,.0f}원")
print(f"8월 최저가: {min_price:,.0f}원")
print(f"변동성: {volatility:.2f}%")
```

**예상 출력**:
```
8월 총 시간봉: 744개
데이터 소스: db
8월 최고가: 98,500,000원
8월 최저가: 85,200,000원
변동성: 15.61%
```

### Example 4: 실시간 차트 업데이트 (캐시 활용)

```python
import asyncio

async def update_chart_realtime():
    """실시간 차트 업데이트 (캐시 효과 확인)"""

    while True:
        # 최신 100개 1분봉 조회 (캐시 활용)
        response = await provider.get_candles(
            symbol="KRW-BTC",
            timeframe="1m",
            count=100
        )

        print(f"캔들 수: {response.total_count}, "
              f"소스: {response.data_source}, "
              f"응답시간: {response.response_time_ms:.2f}ms")

        # 최신 가격 표시
        latest_candle = response.candles[-1]
        print(f"현재가: {latest_candle.trade_price:,.0f}원")

        # 5초 대기 (캐시 효과 확인)
        await asyncio.sleep(5)

# 실행
await update_chart_realtime()
```

**예상 출력**:
```
캔들 수: 100, 소스: api, 응답시간: 156.34ms
현재가: 95,200,000원
캔들 수: 100, 소스: cache, 응답시간: 8.12ms  # 캐시 히트!
현재가: 95,205,000원
캔들 수: 100, 소스: cache, 응답시간: 7.89ms  # 캐시 히트!
현재가: 95,210,000원
```

### Example 5: 백테스팅용 대량 데이터 (청크 처리)

```python
async def backtest_data_collection():
    """백테스팅용 대량 데이터 수집 (청크 자동 분할)"""

    # 2년간 5분봉 데이터 (약 200,000개 → 자동 청크 분할)
    start_time = datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    print("대량 데이터 수집 시작...")
    start_perf = time.perf_counter()

    response = await provider.get_candles(
        symbol="KRW-BTC",
        timeframe="5m",
        start_time=start_time,
        end_time=end_time
    )

    elapsed_time = (time.perf_counter() - start_perf) * 1000

    print(f"수집 완료!")
    print(f"총 캔들 수: {response.total_count:,}개")
    print(f"데이터 소스: {response.data_source}")
    print(f"총 소요 시간: {elapsed_time:,.2f}ms")
    print(f"평균 처리 속도: {response.total_count / (elapsed_time / 1000):,.0f}개/초")

    # 기간별 수익률 분석
    monthly_returns = calculate_monthly_returns(response.candles)
    print(f"월평균 수익률: {sum(monthly_returns) / len(monthly_returns):.2f}%")

await backtest_data_collection()
```

**예상 출력**:
```
대량 데이터 수집 시작...
수집 완료!
총 캔들 수: 210,240개
데이터 소스: mixed
총 소요 시간: 45,230.56ms
평균 처리 속도: 4,648개/초
월평균 수익률: 2.34%
```

---

## 🎛️ Convenience Methods

### `get_latest_candles()`

```python
async def get_latest_candles(
    symbol: str,
    timeframe: str,
    count: int = 200
) -> CandleDataResponse:
    """최신 캔들 조회 (get_candles의 간편 버전)"""

# 사용 예시
response = await provider.get_latest_candles("KRW-BTC", "15m", 50)
```

### `get_stats()`

```python
def get_stats() -> dict:
    """서비스 통계 조회"""

# 사용 예시
stats = provider.get_stats()
print(f"총 요청: {stats['total_requests']}")
print(f"캐시 히트율: {stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100:.1f}%")
print(f"평균 응답시간: {stats['average_response_time_ms']:.2f}ms")
```

**반환값**:
```python
{
    'total_requests': 1523,
    'cache_hits': 891,
    'cache_misses': 632,
    'api_requests': 234,
    'average_response_time_ms': 87.34,
    'supported_timeframes': ['1s', '1m', ..., '1y'],
    'active_cache_entries': 45,
    'last_successful_request': '2024-09-10T14:23:45Z'
}
```

### `get_supported_timeframes()`

```python
def get_supported_timeframes() -> List[str]:
    """지원하는 타임프레임 목록"""

# 사용 예시
timeframes = provider.get_supported_timeframes()
print(f"지원 타임프레임: {len(timeframes)}개")
print(timeframes)
```

**반환값**:
```python
['1s', '1m', '3m', '5m', '10m', '15m', '30m', '60m', '240m',
 '1h', '4h', '1d', '1w', '1M', '1y']
```

### `get_cache_stats()`

```python
def get_cache_stats() -> dict:
    """캐시 통계 조회"""

# 사용 예시
cache_stats = provider.get_cache_stats()
print(f"캐시 사용량: {cache_stats['memory_usage_mb']:.1f}MB")
print(f"히트율: {cache_stats['hit_rate']:.1f}%")
```

**반환값**:
```python
{
    'total_entries': 45,
    'memory_usage_mb': 23.7,
    'hit_rate': 84.3,
    'average_ttl_remaining': 31.2,
    'evicted_entries': 12,
    'expired_entries': 8
}
```

---

## 🚨 Error Handling

### Exception Types

```python
# 사용자 입력 오류
try:
    response = await provider.get_candles("INVALID", "1m", count=100)
except ValidationError as e:
    print(f"입력 오류: {e}")

# 미래 시간 요청
try:
    future_time = datetime.now(timezone.utc) + timedelta(days=1)
    response = await provider.get_candles("KRW-BTC", "1m", start_time=future_time, count=100)
except ValidationError as e:
    print(f"미래 시간 요청 불가: {e}")

# Rate Limit (자동 재시도)
try:
    response = await provider.get_candles("KRW-BTC", "1m", count=100)
    # 자동으로 지수 백오프 재시도 (최대 3회)
except RateLimitError as e:
    print(f"Rate Limit 초과 (재시도 실패): {e}")

# 네트워크 오류 (자동 재시도)
try:
    response = await provider.get_candles("KRW-BTC", "1m", count=100)
    # 자동으로 선형 백오프 재시도 (최대 3회)
except NetworkError as e:
    print(f"네트워크 연결 실패: {e}")
```

### Graceful Degradation

```python
# API 실패시 DB 폴백
response = await provider.get_candles("KRW-BTC", "5m", count=100)

if response.data_source == "db" and response.success:
    print("API 실패했지만 DB에서 데이터 제공")
elif response.data_source == "cache" and response.success:
    print("네트워크 문제로 캐시 데이터 제공")
elif not response.success:
    print(f"모든 소스 실패: {response.error_message}")
```

---

## ⚡ Performance Guidelines

### Response Time Targets

| 요청 크기 | 목표 응답 시간 | 캐시 히트시 |
|-----------|----------------|-------------|
| 100개 캔들 | < 50ms | < 10ms |
| 1,000개 캔들 | < 500ms | < 50ms |
| 10,000개 캔들 | < 5,000ms | < 500ms |

### Best Practices

1. **캐시 활용**: 동일한 요청은 60초간 캐시에서 즉시 반환
2. **적절한 청크 크기**: 200개 이하로 요청시 단일 처리, 초과시 자동 분할
3. **시간 범위 최적화**: 불필요하게 큰 범위 요청 지양
4. **에러 처리**: 자동 재시도를 신뢰하되, 최종 실패시 대안 로직 준비

### Memory Usage

- **캐시 한계**: 최대 100MB
- **청크 처리**: 메모리 사용량 제한
- **자동 정리**: 만료된 캐시 엔트리 자동 삭제

---

## 🔗 Factory Functions

### Synchronous Factory

```python
def create_candle_data_provider(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """CandleDataProvider 팩토리 함수 (동기 버전)"""

# 사용 예시
provider = create_candle_data_provider()  # 기본 설정으로 생성
```

### Asynchronous Factory (with Initialization)

```python
async def create_candle_data_provider_async(
    db_manager: Optional[DatabaseManager] = None,
    upbit_client: Optional[UpbitPublicClient] = None
) -> CandleDataProvider:
    """CandleDataProvider 팩토리 함수 (비동기 버전, 초기화 포함)"""

# 사용 예시
provider = await create_candle_data_provider_async()  # 완전 초기화된 인스턴스
```

---

## 📊 Integration with Main Program

### UI Layer Integration

```python
# PyQt6 차트 위젯에서 사용
class CandleChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.provider = create_candle_data_provider()

    async def update_chart_data(self, symbol: str, timeframe: str):
        """차트 데이터 업데이트"""
        response = await self.provider.get_candles(symbol, timeframe, count=200)

        if response.success:
            self.plot_candles(response.candles)
            self.update_status(f"데이터 로딩 완료 ({response.response_time_ms:.0f}ms)")
        else:
            self.show_error(response.error_message)
```

### Application Layer Integration

```python
# 자동매매 전략에서 사용
class TradingStrategy:
    def __init__(self):
        self.candle_provider = create_candle_data_provider()

    async def analyze_market(self, symbol: str) -> bool:
        """시장 분석 (최근 100개 5분봉)"""
        response = await self.candle_provider.get_candles(symbol, "5m", count=100)

        if not response.success:
            logger.error(f"캔들 데이터 조회 실패: {response.error_message}")
            return False

        # RSI, MACD 등 기술적 분석
        rsi = self.calculate_rsi(response.candles)
        return rsi < 30  # 과매도 진입 신호
```

이제 API 명세서가 완성되었습니다. 다음 단계인 테스트 전략 및 검증 계획을 수립할까요?
