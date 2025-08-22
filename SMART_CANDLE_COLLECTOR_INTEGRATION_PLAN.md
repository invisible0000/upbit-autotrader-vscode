# 스마트 캔들 콜렉터 → Smart Data Provider V3.0 통합 계획

## 🏗️ 아키텍처 결정

### ✅ 권장: Smart Data Provider V3.0 확장
스마트 캔들 콜렉터를 **Smart Data Provider의 새로운 기능**으로 통합하는 것이 최적입니다.

### 📋 통합 이유

1. **기존 인프라 활용**
   - Smart Data Provider는 이미 캔들 데이터 처리의 핵심
   - SQLite 캐시 시스템 완비
   - Smart Router 연동 완료

2. **DDD 아키텍처 준수**
   - Repository 패턴 이미 적용
   - CandleRepositoryInterface 의존성 주입 구조
   - DatabaseManager 통합 관리

3. **중복 방지**
   - 캔들 수집 로직 중앙화
   - 캐시 시스템 통합 활용
   - API 호출 최적화 공유

## 🔧 구체적 통합 방안

### Phase 1: Smart Data Provider 확장 (20분)

#### 1.1 수집 상태 관리 추가
```python
# upbit_auto_trading/infrastructure/market_data_backbone/smart_data_provider/processing/
# 새 파일: collection_status_manager.py

class CollectionStatusManager:
    """캔들 수집 상태 관리자 - Smart Data Provider 확장"""

    def __init__(self, candle_repository: CandleRepositoryInterface):
        self.candle_repository = candle_repository
        self.logger = create_component_logger("CollectionStatusManager")

    async def ensure_candle_range(self, symbol: str, timeframe: str,
                                start_time: datetime, end_time: datetime) -> List[Dict]:
        """스마트 수집: 빈 캔들과 미수집 캔들 구분 처리"""

        # 1. 예상 캔들 시간 생성
        expected_times = self._generate_expected_times(start_time, end_time, timeframe)

        # 2. 수집 상태 확인
        status_map = await self._check_collection_status(symbol, timeframe, expected_times)

        # 3. 미수집 캔들 재수집
        await self._collect_missing_candles(symbol, timeframe, status_map)

        # 4. 최종 데이터 구성 (실제 + 채움)
        return await self._build_continuous_data(symbol, timeframe, expected_times)
```

#### 1.2 Smart Data Provider 메서드 확장
```python
# upbit_auto_trading/infrastructure/market_data_backbone/smart_data_provider/core/smart_data_provider.py

class SmartDataProvider:

    def __init__(self, ...):
        # 기존 초기화...
        self.collection_status_manager = CollectionStatusManager(self.candle_repository)

    # 새 메서드 추가
    async def get_continuous_candles(self, symbol: str, timeframe: str,
                                   start_time: datetime, end_time: datetime,
                                   include_empty: bool = True) -> DataResponse:
        """연속성 보장된 캔들 데이터 제공"""

        try:
            # 스마트 수집으로 완전한 데이터 확보
            continuous_data = await self.collection_status_manager.ensure_candle_range(
                symbol, timeframe, start_time, end_time
            )

            if not include_empty:
                # 실제 거래 캔들만 필터링 (지표 계산용)
                continuous_data = [c for c in continuous_data if c.get('is_real_trade', True)]

            return DataResponse(
                success=True,
                data=continuous_data,
                metadata=ResponseMetadata(
                    source="smart_collection",
                    cache_hit=True,  # 스마트 수집은 캐시 기반
                    records_count=len(continuous_data),
                    data_quality="CONTINUOUS_GUARANTEED"
                )
            )

        except Exception as e:
            self.logger.error(f"연속 캔들 수집 실패: {symbol} {timeframe}, {e}")
            return DataResponse(success=False, error=str(e))
```

### Phase 2: 수집 상태 DB 스키마 확장 (10분)

#### 2.1 기존 market_data.sqlite3 확장
```sql
-- Smart Data Provider가 사용하는 DB에 추가
CREATE TABLE IF NOT EXISTS candle_collection_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    target_time TEXT NOT NULL,
    collection_status TEXT NOT NULL, -- 'COLLECTED', 'EMPTY', 'PENDING', 'FAILED'
    last_attempt_at TEXT,
    attempt_count INTEGER DEFAULT 0,
    api_response_code INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, timeframe, target_time)
);

CREATE INDEX IF NOT EXISTS idx_collection_status_lookup
ON candle_collection_status(symbol, timeframe, target_time);
```

#### 2.2 Repository 패턴 확장
```python
# upbit_auto_trading/domain/repositories/candle_repository_interface.py 확장

class CandleRepositoryInterface(ABC):
    # 기존 메서드들...

    # 새 메서드 추가
    async def get_collection_status(self, symbol: str, timeframe: str,
                                  target_time: datetime) -> Optional[CollectionStatusRecord]:
        """수집 상태 조회"""
        pass

    async def update_collection_status(self, symbol: str, timeframe: str,
                                     target_time: datetime, status: CollectionStatus,
                                     api_response_code: Optional[int] = None):
        """수집 상태 업데이트"""
        pass
```

### Phase 3: 차트 UI 통합 (15분)

#### 3.1 Chart Service 확장
```python
# upbit_auto_trading/application/services/chart_market_data_service.py

class ChartMarketDataService:

    def __init__(self, smart_data_provider: SmartDataProvider):
        self.smart_data_provider = smart_data_provider

    async def get_chart_data(self, symbol: str, timeframe: str,
                           start_time: datetime, end_time: datetime) -> Tuple[List[Dict], List[Dict]]:
        """차트용과 지표용 데이터 분리 제공"""

        # 차트용: 연속성 보장 (빈 캔들 포함)
        chart_response = await self.smart_data_provider.get_continuous_candles(
            symbol, timeframe, start_time, end_time, include_empty=True
        )

        # 지표용: 정확성 보장 (실제 거래만)
        indicator_response = await self.smart_data_provider.get_continuous_candles(
            symbol, timeframe, start_time, end_time, include_empty=False
        )

        return chart_response.data, indicator_response.data
```

#### 3.2 finplot 위젯 적용
```python
# upbit_auto_trading/ui/desktop/components/chart_widget.py

class ChartWidget:

    async def load_and_render_chart(self, symbol: str, timeframe: str, period: int):
        """스마트 수집 기반 차트 렌더링"""

        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=period)

        # Smart Data Provider에서 연속 데이터 획득
        chart_data, indicator_data = await self.chart_service.get_chart_data(
            symbol, timeframe, start_time, end_time
        )

        # finplot 렌더링
        self.render_continuous_chart(chart_data, indicator_data)

    def render_continuous_chart(self, chart_data: List[Dict], indicator_data: List[Dict]):
        """연속성과 정확성 모두 보장하는 렌더링"""

        # 1. 연속 캔들스틱 (차트 연속성)
        chart_df = pd.DataFrame(chart_data)
        fplt.candlestick_ochl(chart_df[['opening_price', 'trade_price', 'high_price', 'low_price']])

        # 2. 정확한 지표 (매매 정확성)
        indicator_df = pd.DataFrame(indicator_data)
        sma20 = indicator_df['trade_price'].rolling(20).mean()
        fplt.plot(sma20, color='blue', legend='SMA(20)')

        # 3. 빈 캔들 시각적 구분
        for i, candle in enumerate(chart_data):
            if not candle.get('is_real_trade', True):
                fplt.add_line((i, candle['low_price']), (i, candle['high_price']),
                             color='gray', style='--', width=1, alpha=0.5)
```

## 🎯 통합 후 사용법

### 기존 코드 최소 변경으로 업그레이드

#### Before (기존):
```python
# 기존 Smart Data Provider 사용
response = await smart_data_provider.get_candles(symbol, timeframe, count=100)
candles = response.data
```

#### After (확장):
```python
# 스마트 수집 기능 활용
chart_response = await smart_data_provider.get_continuous_candles(
    symbol, timeframe, start_time, end_time, include_empty=True
)
indicator_response = await smart_data_provider.get_continuous_candles(
    symbol, timeframe, start_time, end_time, include_empty=False
)

chart_candles = chart_response.data      # 연속성 보장
indicator_candles = indicator_response.data  # 정확성 보장
```

## ✅ 통합의 장점

1. **기존 생태계 활용**
   - Smart Data Provider V3.0의 성숙한 캐시 시스템
   - 이미 검증된 Repository 패턴
   - Smart Router 최적화 알고리즘

2. **점진적 적용**
   - 기존 `get_candles()` 메서드는 그대로 유지
   - 새로운 `get_continuous_candles()` 메서드 추가
   - 하위 호환성 100% 보장

3. **성능 최적화**
   - 기존 SQLite 캐시와 메모리 캐시 활용
   - 중복 API 호출 완전 방지
   - Smart Router의 지능형 라우팅

4. **DDD 아키텍처 준수**
   - Repository 인터페이스 확장
   - 의존성 주입 패턴 유지
   - 계층 분리 원칙 준수

## 🚀 다음 단계

1. **즉시 구현**: `collection_status_manager.py` 생성
2. **DB 확장**: 수집 상태 테이블 추가
3. **Repository 확장**: 인터페이스에 수집 상태 메서드 추가
4. **Smart Data Provider 확장**: `get_continuous_candles()` 메서드 추가

**결론**: 스마트 캔들 콜렉터는 독립적인 새 모듈이 아닌, **Smart Data Provider V3.0의 자연스러운 확장 기능**으로 구현하는 것이 최적입니다! 🎯
