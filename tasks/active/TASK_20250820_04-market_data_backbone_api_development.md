# 📋 TASK_20250820_04: Market Data Backbone API 개발

## 🎯 태스크 목표
- **주요 목표**: 3-Layer 아키텍처를 통합하여 전체 시스템에 단일 마켓 데이터 API 제공
- **완료 기준**: 스크리너, 백테스터, 차트뷰어 등이 하나의 API로 모든 데이터 요구사항 해결

## 📊 Backbone API의 역할 정의

### 🎯 핵심 책임
1. **순수 데이터 제공**: 마켓 데이터의 효율적 추상화된 API만 제공
2. **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 요청하여 사용
3. **투명한 최적화**: 내부 3-Layer가 알아서 최적화, 사용자는 모름
4. **단순한 인터페이스**: 복잡한 사용 사례별 API 없이 기본 데이터 API만
5. **시스템 상태 조회**: 모니터링을 위한 읽기 전용 상태 API
6. **이벤트 버스 통합**: 실거래 우선순위 보장 + 리소스 관리 (하이브리드)

### 🔗 클라이언트별 사용 예시

#### 차트뷰어의 사용법
```python
class ChartViewer:
    async def load_chart(self, symbol: str, timeframe: str):
        # 차트가 필요한 만큼만 직접 요청
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        candles = await market_api.get_candle_data(symbol, timeframe, start_time, end_time)
        # 차트가 알아서 렌더링 로직 처리
        self.render_chart(candles)

    async def update_realtime(self, symbol: str):
        # 실시간 데이터가 필요하면 직접 요청
        ticker = await market_api.get_ticker_data(symbol)
        self.update_price_display(ticker)
```

#### 스크리너의 사용법
```python
class Screener:
    async def scan_markets(self, symbols: List[str]):
        # 스크리너가 필요한 데이터만 병렬 요청
        tasks = [market_api.get_ticker_data(symbol) for symbol in symbols]
        tickers = await asyncio.gather(*tasks)

        # 스크리너가 알아서 분석 로직 처리
        filtered_symbols = self.apply_filters(tickers)
        return filtered_symbols
```

#### 백테스터의 사용법
```python
class Backtester:
    async def run_backtest(self, strategy: Strategy, period: Period):
        # 백테스터가 필요한 기간만 요청 (이벤트 버스 통과)
        candles = await market_api.get_candle_data(
            strategy.symbol, strategy.timeframe, period.start, period.end,
            priority=Priority.LOW  # 백테스트는 낮은 우선순위
        )

        # 백테스터가 알아서 시뮬레이션 로직 처리
        results = self.simulate_strategy(strategy, candles)
        return results
```

#### 실거래봇의 사용법
```python
class TradingBot:
    async def check_market_signal(self, symbol: str):
        # 실거래는 최고 우선순위로 이벤트 버스 우회
        ticker = await market_api.get_ticker_data(
            symbol, priority=Priority.CRITICAL
        )

        # 실거래봇이 알아서 매매 신호 판단
        signal = self.analyze_signal(ticker)
        return signal
```

## 🛠️ 이벤트 버스 통합 전략

### 🎯 **하이브리드 접근: Critical Path + Resource Management**

#### **Critical Path (이벤트 버스 제외)**
```python
# 실거래와 긴급 데이터는 이벤트 버스 우회
Priority.CRITICAL: 실거래봇 데이터 요청
Priority.HIGH: 실시간 차트, 알림 시스템
→ 직접 마켓 데이터 백본 접근 (최고 성능)
```

#### **Resource Management (이벤트 버스 관리)**
```python
# 리소스 집약적 작업은 이벤트 버스로 제어
Priority.NORMAL: 일반 스크리닝, 차트 로딩
Priority.LOW: 백테스트, 대용량 데이터 분석
→ 이벤트 버스 통과 (시스템 보호)
```

### 🔄 **우선순위 기반 라우팅**

```python
from enum import Enum

class Priority(Enum):
    CRITICAL = 0  # 실거래봇 (이벤트 버스 우회)
    HIGH = 1      # 실시간 모니터링 (이벤트 버스 우회)
    NORMAL = 2    # 일반 요청 (이벤트 버스 통과)
    LOW = 3       # 백그라운드 작업 (이벤트 버스 엄격 제어)

class MarketDataAPI:
    async def get_ticker_data(
        self,
        symbol: str,
        priority: Priority = Priority.NORMAL
    ) -> Ticker:
        if priority in [Priority.CRITICAL, Priority.HIGH]:
            # Critical Path: 이벤트 버스 우회
            return await self._direct_access.get_ticker(symbol)
        else:
            # Resource Management: 이벤트 버스 통과
            return await self._event_bus_access.get_ticker(symbol)
```

### ⚡ **시스템 보호 메커니즘**

```python
class SystemLoadManager:
    async def check_resource_availability(self, priority: Priority) -> bool:
        """시스템 부하에 따른 요청 승인/거부"""

        current_load = await self._get_system_load()

        if current_load > 90:
            # 극도로 바쁠 때: CRITICAL만 허용
            return priority == Priority.CRITICAL
        elif current_load > 70:
            # 바쁠 때: LOW 우선순위 차단
            return priority != Priority.LOW
        else:
            # 여유로울 때: 모든 요청 허용
            return True
```

### 🎛️ **이벤트 버스 통합 인터페이스**

```python
class EventBusIntegration:
    """마켓 데이터 백본의 이벤트 버스 통합"""

    async def publish_data_request(self, request: DataRequest) -> str:
        """데이터 요청을 이벤트 버스에 발행 (LOW/NORMAL 우선순위)"""

    async def subscribe_to_system_events(self) -> None:
        """시스템 이벤트 구독 (CPU 사용률, 메모리 경고 등)"""

    async def emergency_throttle(self) -> None:
        """비상 상황 시 LOW 우선순위 요청 일시 중단"""
```

## 🛠️ 체계적 작업 절차

### Phase 1: 순수 데이터 API 설계
- [ ] 1.1 기본 데이터 API 인터페이스 정의 (캔들, 티커, 호가창, 체결)
- [ ] 1.2 우선순위 기반 요청 설계 (Priority.CRITICAL ~ LOW)
- [ ] 1.3 표준 데이터 모델 정의 (Candle, Ticker, Orderbook, Trade)
- [ ] 1.4 시스템 상태 조회 API 설계 (모니터링 전용)

### Phase 2: 이벤트 버스 통합 설계
- [ ] 2.1 Critical Path 설계 (이벤트 버스 우회 경로)
- [ ] 2.2 Resource Management 설계 (이벤트 버스 통과 경로)
- [ ] 2.3 시스템 부하 감지 및 스로틀링 로직
- [ ] 2.4 우선순위 기반 라우팅 구현

### Phase 3: 하이브리드 백본 구현
- [ ] 3.1 우선순위별 이중 경로 구현 (직접 접근 + 이벤트 버스)
- [ ] 3.2 시스템 보호 메커니즘 구현
- [ ] 3.3 실거래 우선순위 보장 로직
- [ ] 3.4 동적 부하 조절 시스템

### Phase 4: 시스템 안정성 및 성능
- [ ] 4.1 실거래 시나리오 우선순위 테스트
- [ ] 4.2 시스템 과부하 상황 시뮬레이션
- [ ] 4.3 이벤트 버스 장애 시 fallback 동작 검증
- [ ] 4.4 메모리 및 CPU 사용량 최적화

### Phase 5: 운영 및 모니터링
- [ ] 5.1 우선순위별 성능 메트릭 수집
- [ ] 5.2 이벤트 버스 통합 상태 대시보드
- [ ] 5.3 실거래 우선순위 보장 모니터링
- [ ] 5.4 자동 부하 조절 및 경고 시스템

## 🛠️ 핵심 파일별 상세 설계

### 1. `market_data_api.py` - 메인 API
```python
class MarketDataAPI:
    """
    순수한 마켓 데이터 제공 API (이벤트 버스 하이브리드 통합)

    특징:
    - 우선순위 기반 이중 경로 (Critical Path + Resource Management)
    - 실거래 우선순위 보장 (CRITICAL/HIGH = 이벤트 버스 우회)
    - 시스템 보호 (NORMAL/LOW = 이벤트 버스 통과)
    - 단순하고 명확한 데이터 API
    """

    def __init__(self):
        self._backbone_manager = BackboneManager()
        self._direct_access = DirectDataAccess()      # Critical Path
        self._event_bus_access = EventBusDataAccess() # Resource Management

    # 우선순위 기반 마켓 데이터 API
    async def get_candle_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        priority: Priority = Priority.NORMAL
    ) -> List[Candle]:
        """캔들 데이터 조회 (우선순위 기반 라우팅)"""

    async def get_ticker_data(
        self,
        symbol: str,
        priority: Priority = Priority.NORMAL
    ) -> Ticker:
        """현재 티커 데이터 조회 (우선순위 기반 라우팅)"""

    async def get_orderbook_data(
        self,
        symbol: str,
        priority: Priority = Priority.NORMAL
    ) -> Orderbook:
        """호가창 데이터 조회 (우선순위 기반 라우팅)"""

    async def get_trade_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        priority: Priority = Priority.NORMAL
    ) -> List[Trade]:
        """체결 내역 조회 (우선순위 기반 라우팅)"""

    # 시스템 상태 조회 (모니터링 전용)
    async def get_system_status(self) -> SystemStatus:
        """시스템 상태 조회 (이벤트 버스 부하 포함)"""

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 지표 조회 (우선순위별 통계 포함)"""
```

### 2. `backbone_manager.py` - 생명주기 관리
```python
class BackboneManager:
    """
    3-Layer 아키텍처의 생명주기 및 내부 관리

    책임:
    - Layer 간 의존성 주입 (사용자 노출 안됨)
    - 내부 설정 자동 관리 (사용자 개입 불가)
    - 시스템 상태 모니터링 (조회만 가능)
    - 우아한 종료 처리
    """

    async def initialize(self) -> None:
        """전체 백본 초기화 (Layer 1 → 2 → 3 순서, 자동)"""

    async def get_system_health(self) -> SystemHealth:
        """시스템 상태 조회 (읽기 전용)"""

    async def get_layer_status(self) -> Dict[str, LayerStatus]:
        """각 Layer 상태 조회 (읽기 전용)"""

    async def shutdown(self) -> None:
        """우아한 종료 (Layer 3 → 2 → 1 순서, 자동)"""
```

### 3. `__init__.py` - 통합 엔트리포인트
```python
"""
Market Data Backbone - 통합 마켓 데이터 시스템

사용법:
    from upbit_auto_trading.infrastructure.market_data_backbone import MarketDataAPI

    api = await MarketDataAPI.create_default()
    data = await api.get_screening_data(request)
"""

from .market_data_api import MarketDataAPI
from .backbone_manager import BackboneManager
from .interfaces.market_data_api import IMarketDataAPI
from .config.backbone_config import BackboneConfig

# 편의 함수들
async def create_default_api() -> MarketDataAPI:
    """기본 설정으로 MarketDataAPI 생성"""

async def create_configured_api(config_path: str) -> MarketDataAPI:
    """설정 파일 기반 MarketDataAPI 생성"""

# 버전 정보
__version__ = "1.0.0"
__all__ = ["MarketDataAPI", "BackboneManager", "IMarketDataAPI", "BackboneConfig"]
```

### 4. `config/backbone_config.py` - 통합 설정
```python
@dataclass
class BackboneConfig:
    """백본 시스템 내부 설정 (자동 관리, 사용자 개입 없음)"""

    # 자동 감지 및 최적화
    auto_optimization: bool = True
    environment_detection: bool = True  # dev/prod 자동 감지

    # 시스템 안정성
    circuit_breaker_enabled: bool = True
    auto_retry_enabled: bool = True
    fallback_mode_enabled: bool = True

    # 리소스 제한 (시스템이 자동 관리)
    max_concurrent_requests: int = 100
    memory_limit_mb: int = 2048

    @classmethod
    def create_auto_config(cls) -> "BackboneConfig":
        """시스템 환경을 자동 분석하여 최적 설정 생성"""
        # 하드웨어 스펙, 네트워크 환경 등을 자동 감지
        return cls()
```

## 🔗 Layer 간 협력 흐름

### 일반적인 데이터 요청 흐름 (우선순위 기반)
```
클라이언트 (차트뷰어, 스크리너, 백테스터, 실거래봇)
    ↓ (필요한 데이터 + 우선순위 지정)
MarketDataAPI.get_xxx_data(symbol, ..., priority=Priority.XXX)
    ↓ (우선순위 기반 라우팅)
┌─ CRITICAL/HIGH → DirectDataAccess (이벤트 버스 우회)
└─ NORMAL/LOW → EventBusDataAccess (리소스 관리)
    ↓ (투명한 3-Layer 처리)
Layer 1,2,3 (캐시/DB/API 자동 조합)
    ↓ (단순한 데이터 반환)
클라이언트 (받은 데이터로 알아서 비즈니스 로직 처리)
```

### 실거래 우선순위 보장 흐름 (Critical Path)
```
실거래봇
    ↓ (긴급 티커 데이터 요청 + priority=Priority.CRITICAL)
MarketDataAPI.get_ticker_data(symbol, priority=CRITICAL)
    ↓ (이벤트 버스 완전 우회)
DirectDataAccess → Layer 1,2,3 직접 접근
    ↓ (최고 성능, 지연 없음)
실거래봇 (즉시 매매 신호 판단)

vs

백테스터
    ↓ (대용량 캔들 데이터 요청 + priority=Priority.LOW)
MarketDataAPI.get_candle_data(symbol, timeframe, start, end, priority=LOW)
    ↓ (이벤트 버스 통과, 시스템 부하 체크)
EventBusDataAccess → 부하 허용 시에만 처리
    ↓ (시스템 보호, 실거래 방해 없음)
백테스터 (여유 있을 때 처리)
```

## 🎯 클라이언트별 최적화 (각자 알아서)

### 1. 차트뷰어 (자율적 데이터 관리)
- **자체 캐싱**: 차트가 필요한 만큼 데이터 요청하고 자체 캐싱
- **실시간 업데이트**: 필요시 ticker_data() 주기적 호출로 실시간 구현
- **메모리 관리**: 차트가 알아서 불필요한 데이터 정리
- **렌더링 최적화**: 받은 데이터로 차트가 알아서 부드러운 렌더링

### 2. 스크리너 (자율적 분석)
- **병렬 요청**: 여러 심볼 ticker_data() 동시 요청으로 성능 최적화
- **필터링 로직**: 받은 데이터로 스크리너가 알아서 조건 필터링
- **결과 캐싱**: 스크리너가 알아서 분석 결과 관리
- **알림 처리**: 조건 만족 시 스크리너가 알아서 알림 발송

### 3. 백테스터 (자율적 시뮬레이션)
- **청크 처리**: 대용량 데이터를 백테스터가 알아서 청크별 처리
- **메모리 효율**: 필요한 구간만 요청하여 메모리 절약
- **진행률 관리**: 백테스터가 알아서 사용자에게 진행률 표시
- **결과 저장**: 시뮬레이션 결과를 백테스터가 알아서 관리

## 🎯 성공 기준
- ✅ **극도의 단순화**: 기본 데이터 API 4개만 제공 (candle, ticker, orderbook, trade)
- ✅ **클라이언트 자율성**: 각 프로그램이 필요한 데이터를 스스로 요청하여 사용
- ✅ **실거래 우선순위**: CRITICAL/HIGH 우선순위로 이벤트 버스 우회, 최고 성능 보장
- ✅ **시스템 보호**: NORMAL/LOW 우선순위로 이벤트 버스 통과, 리소스 관리
- ✅ **투명한 최적화**: 내부 3-Layer가 알아서 최적화, 사용자는 존재도 모름
- ✅ **설정 제로**: 우선순위 매개변수 외 어떤 복잡한 설정도 필요 없음
- ✅ **하이브리드 통합**: 이벤트 버스 장점(리소스 관리) + 직접 접근 장점(성능)

## 🚀 개발 우선순위
1. **Phase 1**: 기본 데이터 API 4개 구현 (캔들, 티커, 호가창, 체결)
2. **Phase 2**: 내부 3-Layer 투명한 통합
3. **Phase 3**: 자동 최적화 및 에러 복구
4. **Phase 4**: 시스템 안정성 및 성능 검증
5. **Phase 5**: 모니터링 도구 (조회 전용)

---
**의존성**: TASK_20250820_01,02,03 모든 Layer 완료 후 시작
**통합 대상**: 모든 클라이언트가 단순한 4개 API로 자율적 사용
**예상 소요시간**: 1-2일 (3-Layer 완료 후)
**핵심 가치**: 극도로 단순한 데이터 API + 클라이언트 완전 자율성
