# 자산 스크리너 재설계 문서

## 개요

기존 스크리너의 복잡성 문제를 해결하기 위해 단순하고 안정적인 아키텍처로 재설계합니다. 모든 기능을 단계별로 구현하여 각 단계에서 안정성을 확보합니다.

## 아키텍처

### 핵심 설계 원칙

1. **단순성 우선**: 복잡한 비동기 처리 대신 단순한 동기 처리
2. **안정성 우선**: 오류 발생 시 전체 시스템이 중단되지 않도록 격리
3. **사용자 경험 우선**: 명확한 피드백과 직관적인 인터페이스
4. **점진적 개발**: 기본 기능부터 단계적으로 확장

### UI 레이아웃 설계

```
스크리너 화면 레이아웃 (좌우 1:3 분할):

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SimpleScreenerTab                                 │
├─────────────────────┬───────────────────────────────────────────────────────┤
│     좌측 (1)        │                    우측 (3)                          │
│                     │                                                       │
│ ┌─────────────────┐ │ ┌───────────────────────────────────────────────────┐ │
│ │   코인 리스트    │ │ │              스크리닝 결과                        │ │
│ │  (3 비율)       │ │ │            + 상단 필터                           │ │
│ │ 시장: [KRW▼] [✓]즐겨찾기만 │ │          (1 비율)                               │ │
│ │ ┌─────────────┐   │ │ │                                                   │ │
│ │ │ KRW-BTC     │   │ │ │                                                   │ │
│ │ │ KRW-ETH     │   │ │ │                                                   │ │
│ │ │ KRW-ADA     │   │ │ │                                                   │ │
│ │ │ ...         │   │ │ │                                                   │ │
│ │ └─────────────┘   │ │ │                                                   │ │
│ └─────────────────┘ │ └───────────────────────────────────────────────────┘ │
│                     │                                                       │
│ ┌─────────────────┐ │ ┌───────────────────────────────────────────────────┐ │
│ │   스크린 설정    │ │ │                코인 차트                          │ │
│ │  (3 비율)       │ │ │            (1 비율)                              │ │
│ │ - 지표 선택      │ │ │ - 캔들스틱 차트                                   │ │
│ │ - 빠른 선택      │ │ │ - 거래량 서브플롯                                 │ │
│ │ - 스크롤 가능    │ │ │ - 기술적 지표 오버레이                            │ │
│ └─────────────────┘ │ └───────────────────────────────────────────────────┘ │
│ │   스크린 제어    │ │                                                       │
│ │  (1 비율)       │ │                                                       │
│ │ - 시작/중지      │ │                                                       │
│ │ - 타임프레임     │ │                                                       │
│ │ - 진행바         │ │                                                       │
│ └─────────────────┘ │                                                       │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

### 코인 리스트 위젯 상세 레이아웃

```
┌─────────────────────────────────────┐
│ 시장: [KRW ▼] [✓] 즐겨찾기만 보기    │  ← 한 줄 배치로 공간 절약
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ ⭐ KRW-BTC  (비트코인)           │ │  ← 즐겨찾기 코인 상위 표시
│ │ ⭐ KRW-ETH  (이더리움)           │ │
│ │ ─────────────────────────────── │ │
│ │    KRW-ADA  (에이다)            │ │  ← 일반 코인들
│ │    KRW-DOT  (폴카닷)            │ │
│ │    KRW-LINK (체인링크)          │ │
│ │    ...                          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### 시스템 구조

```
새로운 스크리너 구조:

┌─────────────────────────────────────┐
│           UI Layer                  │
│  ┌─────────────────────────────────┐│
│  │    SimpleScreenerTab            ││
│  │  ┌─────────────────────────────┐││
│  │  │  CoinListWidget             │││
│  │  │  ScreenSettingsWidget       │││
│  │  │  ScreenControlWidget        │││
│  │  │  ResultsTableWidget         │││
│  │  │  CoinChartWidget            │││
│  │  └─────────────────────────────┘││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
              │
┌─────────────────────────────────────┐
│         Business Layer              │
│  ┌─────────────────────────────────┐│
│  │    SimpleScreener               ││
│  │  - 기본 필터링 로직              ││
│  │  - 단순한 기술적 분석            ││
│  │  - 즐겨찾기 우선 처리            ││
│  │  - 오류 처리                    ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
              │
┌─────────────────────────────────────┐
│          Data Layer                 │
│  ┌─────────────────────────────────┐│
│  │    SimpleDataCollector          ││
│  │  - 업비트 API 호출              ││
│  │  - 데이터 캐싱                  ││
│  │  - 재시도 로직                  ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## 컴포넌트 및 인터페이스

### 1. SimpleScreenerTab (메인 UI 컴포넌트)

**책임:**
- 전체 레이아웃 관리 (좌우 1:3 분할)
- 하위 위젯들 간의 통신 조정
- 스크리닝 프로세스 전체 제어

**주요 메서드:**
```python
class SimpleScreenerTab:
    def __init__(self)
    def setup_ui(self)
    def setup_layout(self)  # 좌우 분할 레이아웃 설정
    def connect_signals(self)  # 위젯 간 시그널 연결
    def start_screening(self)
    def stop_screening(self)
    def on_coin_selected(self, symbol)  # 차트 업데이트
```

### 2. CoinListWidget (코인 리스트 위젯)

**책임:**
- 시장별 코인 필터링 (기본값: KRW)
- 즐겨찾기 관리
- 코인 선택 처리
- 한 줄 레이아웃으로 공간 절약
- 코인 심벌을 시장 포함 형식으로 표시 (예: KRW-BTC)

**주요 메서드:**
```python
class CoinListWidget:
    def __init__(self)
    def setup_ui(self)  # 한 줄 레이아웃 설정
    def load_coin_list(self)  # 창 열릴 때 모든 코인 로드
    def filter_by_market(self, market="KRW")  # 기본값 KRW
    def format_symbol_display(self, symbol)  # KRW-BTC 형식으로 표시
    def toggle_favorite(self, symbol)
    def get_favorite_coins(self)
    def get_selected_coins(self)
    def refresh_coin_list(self)  # 시장 변경 시 전체 목록 새로고침
```

### 3. ScreenSettingsWidget (스크린 설정 위젯)

**책임:**
- 지표 선택 UI
- 빠른 선택 버튼
- 스크롤 가능한 설정 패널

**주요 메서드:**
```python
class ScreenSettingsWidget:
    def __init__(self)
    def setup_indicators(self)
    def setup_quick_presets(self)
    def get_selected_indicators(self)
    def apply_preset(self, preset_name)
```

### 4. ScreenControlWidget (스크린 제어 위젯)

**책임:**
- 시작/중지 버튼
- 타임프레임/기간 설정
- 진행바 및 상태 표시

**주요 메서드:**
```python
class ScreenControlWidget:
    def __init__(self)
    def setup_controls(self)
    def update_progress(self, current, total, symbol, eta)
    def set_default_timeframe(self)
    def get_timeframe_settings(self)
```

### 5. ResultsTableWidget (결과 테이블 위젯)

**책임:**
- 스크리닝 결과 표시
- 상단 필터 기능
- 정렬 및 즐겨찾기 우선 표시

**주요 메서드:**
```python
class ResultsTableWidget:
    def __init__(self)
    def setup_filter_bar(self)
    def add_result(self, coin_analysis)
    def sort_by_column(self, column, order)
    def apply_filter(self, filter_text)
    def maintain_favorite_priority(self)
```

### 6. CoinChartWidget (코인 차트 위젯)

**책임:**
- mplfinance를 사용한 캔들스틱 차트 표시
- 거래량 서브플롯
- 캔들차트 오버레이 지표 (이동평균, 볼린저밴드)

**주요 메서드:**
```python
class CoinChartWidget:
    def __init__(self)
    def setup_mplfinance_widget(self)  # PyQt6에 matplotlib 임베드
    def load_chart_data(self, symbol, timeframe)
    def display_candlestick_with_volume(self, data)
    def add_moving_averages(self, sma_periods, ema_periods)
    def add_bollinger_bands(self, period=20)
    def clear_chart(self)
```

### 2. SimpleScreener (비즈니스 로직)

**책임:**
- 필터링 로직 실행
- 기술적 지표 계산
- 결과 생성 및 정렬

**주요 메서드:**
```python
class SimpleScreener:
    def __init__(self, data_collector)
    def apply_filters(self, coins, filters)
    def calculate_indicators(self, coin_data)
    def score_coins(self, analyzed_coins)
    def get_recommendations(self, scored_coins)
```

### 3. SimpleDataCollector (데이터 계층)

**책임:**
- 업비트 API 호출
- 증분 데이터 수집 및 공유 DB 병합
- 공유 시장 데이터 DB 관리 (단일 코인-타임프레임당 단일 테이블)
- 데이터 캐싱 및 관리
- 오류 처리 및 재시도

**주요 메서드:**
```python
class SimpleDataCollector:
    def __init__(self)
    def get_coin_list(self)
    def get_ticker_data(self, symbols)
    def get_candle_data_incremental(self, symbol, interval, count)  # 증분 수집
    def check_existing_data_in_shared_db(self, symbol, interval)  # 공유 DB 기존 데이터 확인
    def get_shared_table_name(self, symbol, interval)  # 공유 테이블명 생성
    def merge_data_to_shared_db(self, symbol, interval, new_data)  # 공유 DB 병합
    def get_data_gap(self, symbol, interval, required_period)  # 필요한 데이터 갭 계산
    def ensure_single_table_per_coin_timeframe(self, symbol, interval)  # 단일 테이블 보장
    def clear_cache(self)
```

## 데이터 모델

### 코인 정보
```python
@dataclass
class CoinInfo:
    symbol: str  # 전체 심벌 (예: "KRW-BTC")
    name: str
    market: str  # "KRW", "BTC", "USDT"
    base_currency: str  # 기본 통화 (예: "BTC")
    is_favorite: bool = False
    
    @property
    def display_symbol(self) -> str:
        """UI에 표시할 심벌 형식 (KRW-BTC)"""
        return self.symbol
```

### 스크리닝 설정
```python
@dataclass
class ScreeningSettings:
    timeframe: str = "1d"  # "1m", "5m", "1h", "1d", "1w"
    period: int = 30  # 기간 (일)
    indicators: List[str] = field(default_factory=list)
    liquidity_filter: bool = True
    volume_filter: bool = True
```

### 필터 조건
```python
@dataclass
class ScreeningFilters:
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_volume: Optional[float] = None
    min_market_cap: Optional[float] = None
    rsi_min: Optional[float] = None
    rsi_max: Optional[float] = None
```

### 분석 결과
```python
@dataclass
class CoinAnalysis:
    symbol: str
    name: str
    current_price: float
    volume_24h: float
    market_cap: float
    liquidity_score: float
    # 캔들차트 오버레이 지표만 포함
    sma_5: float
    sma_20: float
    sma_60: float
    ema_12: float
    ema_26: float
    bollinger_upper: float
    bollinger_lower: float
    score: float
    recommendation: str  # "BUY", "HOLD", "SELL"
    is_favorite: bool = False
```

### 진행 상태
```python
@dataclass
class ScreeningProgress:
    total_coins: int
    processed_coins: int
    current_symbol: str
    estimated_time_remaining: int  # 초
    is_running: bool = False
    data_collection_mode: str = "incremental"  # "full", "incremental", "cached"
```

### 데이터 수집 정보
```python
@dataclass
class DataCollectionInfo:
    symbol: str
    timeframe: str
    shared_table_name: str  # 공유 DB 테이블명 (예: "candles_KRW-BTC_1d")
    existing_data_start: Optional[datetime] = None
    existing_data_end: Optional[datetime] = None
    required_start: datetime
    required_end: datetime
    collection_mode: str = "incremental"  # "full", "prepend", "append", "cached"
    api_calls_needed: int = 0
    is_shared_table_exists: bool = False
```

### 공유 DB 테이블 구조
```python
# 테이블명 규칙: candles_{symbol}_{timeframe}
# 예시: candles_KRW-BTC_1d, candles_KRW-ETH_1h, candles_BTC-ETH_5m
# 단일 코인-타임프레임 조합마다 하나의 테이블만 유지
# 다른 기능(백테스팅, 차트 뷰 등)에서도 동일한 테이블 사용

CREATE TABLE candles_{symbol}_{timeframe} (
    timestamp DATETIME PRIMARY KEY,
    open_price DECIMAL(20, 8),
    high_price DECIMAL(20, 8),
    low_price DECIMAL(20, 8),
    close_price DECIMAL(20, 8),
    volume DECIMAL(20, 8),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 오류 처리

### 오류 처리 전략

1. **API 오류**: 재시도 후 실패 시 해당 코인 건너뛰기
2. **데이터 파싱 오류**: 로그 기록 후 다음 코인으로 진행
3. **네트워크 오류**: 사용자에게 알림 후 재시도 옵션 제공
4. **메모리 부족**: 배치 크기 줄여서 재시도

### 오류 복구 메커니즘

```python
class ErrorHandler:
    def handle_api_error(self, error, symbol)
    def handle_parsing_error(self, error, data)
    def handle_network_error(self, error)
    def should_retry(self, error_type, attempt_count)
```

## 테스트 전략

### 단위 테스트
- 각 컴포넌트별 독립적 테스트
- 모의 데이터를 사용한 테스트
- 오류 상황 시뮬레이션

### 통합 테스트
- 실제 API를 사용한 소규모 테스트
- 전체 워크플로우 테스트
- 성능 및 안정성 테스트

### 사용자 테스트
- 실제 사용 시나리오 테스트
- UI/UX 피드백 수집
- 오류 상황 대응 테스트

## 성능 고려사항

### 최적화 전략

1. **배치 처리**: 코인을 작은 그룹으로 나누어 처리
2. **캐싱**: 자주 사용되는 데이터 캐싱
3. **지연 로딩**: 필요한 시점에만 데이터 로드
4. **메모리 관리**: 사용 완료된 데이터 즉시 정리

### 리소스 제한

- 동시 API 호출 수: 최대 5개
- 메모리 사용량: 최대 500MB
- 처리 시간: 코인당 최대 2초
- 전체 처리 시간: 최대 10분

## 보안 고려사항

### API 키 관리
- 환경 변수 또는 설정 파일에 저장
- 메모리에서 즉시 정리
- 로그에 노출 방지

### 데이터 보호
- 민감한 데이터 암호화
- 임시 파일 안전 삭제
- 네트워크 통신 보안

## 배포 및 유지보수

### 배포 전략
1. 기존 스크리너와 병렬 개발
2. 충분한 테스트 후 교체
3. 롤백 계획 준비

### 유지보수 계획
- 정기적인 성능 모니터링
- 사용자 피드백 수집
- 점진적 기능 개선