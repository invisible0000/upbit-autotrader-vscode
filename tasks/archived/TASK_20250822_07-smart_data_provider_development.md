# 📋 TASK_20250822_07: Smart Data Provider 개발

## 🎯 태스크 목표
- **주요 목표**: 마켓 데이터가 DB에 잘 보관되어 효율적으로 제공되는 통합 시스템 구축
- **완료 기준**:
  - ✅ 4개 통합 API (캔들/티커/호가/체결)
  - ✅ SQLite 캔들 자동 캐시 + 메모리 실시간 캐시
  - ✅ 대용량 요청 자동 분할 처리
  - ✅ 우선순위 기반 처리 (실거래 우선)
  - ✅ Smart Router V2.0 완전 활용

## 📊 현재 상황 분석 (2025-08-22 17:50 업데이트)

### ✅ **기반 시스템 현황**
- **Smart Router V2.0** ✅ 완료 - 채널 선택, API 호출, 장애 복구
- **SQLite 스키마** ✅ 준비 - market_data.sqlite3 구조 완성
- **기본 클라이언트** ✅ 완료 - UpbitPublicClient, UpbitWebSocketClient
### 📊 **예상 소요 시간** (수정됨)

### 🔥 **단계별 작업 일정**
1. **Phase 1 - 핵심 구조**: 3일 ✅ **완료**
2. **Phase 2 - 스토리지 통합**: 4일 ✅ **완료**
3. **Phase 3 - 자동화 기능**: 2일 ✅ **완료**
4. **Phase 4 - 통합 테스트**: 1일 ⚠️ **진행 중**
5. **🚨 Phase 4.5 - DDD 아키텍처 수정**: 1일 ❌ **긴급 추가**

### 📈 **총 예상 소요 시간**: **11일** (완료)**Smart Data Provider 구현 현황**
- **Phase 0-3**: ✅ **100% 완료** (핵심 기능 모두 구현)
- **Phase 4**: ✅ **95% 완료** (DDD 아키텍처 수정 완료, 소규모 개선사항 남음)
- **Phase 4.5**: ✅ **100% 완료** (DDD 아키텍처 완전 수정 완료)

#### **✅ 완료된 핵심 기능들**
- 5가지 캔들 요청 방식 (개수, 시간범위, 혼합, 기본, 우선순위)
- RequestSplitter 자동 분할 (300개→분할, 50개→통과)
- 데이터베이스 저장 (기존 심볼 대상)
- 캐시 성능 개선 (66.7% 히트율)
- Smart Router 연동 및 로깅 정확성
- **DDD 아키텍처 완전 준수**: Repository 패턴, DatabaseManager 통합
- **FOREIGN KEY 해결**: 새로운 심볼 자동 등록 기능 구현
- **CandleTableManager 제거**: 레거시 코드 정리 완료

#### **✅ 완료된 개선사항 (2025-08-22)**

**🎉 Priority 1 완료: 오류 처리 개선** ✅
- **심볼 유효성 검증**: 형식, 길이, 특수문자 완전 검증
- **타임프레임 검증**: 업비트 지원 타임프레임만 허용 (1m~1M)
- **개수 범위 검증**: 캔들(1~200), 체결(1~100) 적절한 제한
- **다중 심볼 검증**: 빈 리스트, 과다 요청(50개 이상), 개별 심볼 검증
- **상세 오류 메시지**: 클라이언트가 문제를 즉시 파악할 수 있는 명확한 안내
- **테스트 검증**: 모든 유효성 검증 케이스 통과

**🔍 Priority 2 검토 완료: 체결 데이터 스크리너 활용 분석** ✅
- **활용 가치 평가**: ⭐⭐⭐⭐⭐ 매우 높음 (거래량 급증, 고래 거래 감지)
- **기술적 현실성**: 5-8일 개발 기간, Smart Router 체결 API 선결 조건
- **권장 접근법**: 단계적 구현 (거래량 분석 → 고래 추적 → 모멘텀 분석)
- **시너지 타이밍**: 스크리너 DDD 재개발과 함께 진행 시 최적

#### **⏸️ 보류된 개선사항 (우선순위별)**

**Priority 2: 체결 데이터 지원** ⏸️ **스크리너 재개발 시 함께 고려**
- **현황**: Smart Router에서 체결 API 미지원, 기능 제한적
- **가치**: 스크리너에서 매우 높은 활용 가치 (거래량 급증, 고래 거래 감지)
- **권장**: 별도 태스크로 분리, 스크리너 DDD 재개발과 동시 진행

**Priority 3: 선택적 어댑터** ❌ **구현하지 않음**
- **현황**: `database_adapter.py`, `legacy_client_adapter.py` 문서상 언급
- **판단**: 현재 구조(Repository, SmartRouter 어댑터)가 더 우수
- **결론**: 오버엔지니어링으로 판단, 구현 제외

### 📈 **7규칙 전략 준비도**
- **현재**: ✅ **95% 준비 완료** (DDD 아키텍처 완전 수정, 핵심 기능 모두 완성)
- **완료 후**: 98% 준비 완료 (소규모 개선사항 해결 시)

### 🎯 **Smart Data Provider 역할 정의**

#### **핵심 책임**
- **단일 진입점**: 모든 클라이언트가 하나의 API로 마켓 데이터 접근
- **자동 캐시**: SQLite (캔들) + 메모리 (실시간) 이중 캐시 시스템
- **스마트 분할**: 대용량 요청을 자동으로 적절한 크기로 분할
- **우선순위 처리**: 실거래 > 차트뷰어 > 백테스터 순 처리
- **투명한 최적화**: 내부 복잡성을 클라이언트에서 완전히 숨김

#### **클라이언트별 사용 시나리오**
```
🖥️ 차트뷰어
요청: await provider.get_candles("KRW-BTC", "1m", count=1000, priority=NORMAL)
처리: SQLite 캐시 확인 → 부족한 부분만 Smart Router 요청 → 자동 병합
응답: 1000개 캔들 데이터 (< 2초, 캐시 히트시 < 100ms)

🔍 스크리너
요청: await provider.get_tickers(KRW_symbols, priority=HIGH)
처리: 메모리 캐시 확인 → 최신 데이터 Smart Router 요청 → 빠른 응답
응답: 189개 KRW 마켓 티커 (< 500ms)

📈 백테스터
요청: await provider.get_candles("KRW-BTC", "1m", start="2024-01-01", priority=LOW)
처리: SQLite 우선 조회 → 부족한 부분만 백그라운드 수집 → 점진적 제공
응답: 3개월 데이터 (SQLite 히트시 즉시, API 수집시 진행률 추적)

🤖 실거래봇
요청: await provider.get_tickers(["KRW-BTC"], priority=CRITICAL)
처리: 메모리 캐시 우선 → 1초 이내 데이터면 즉시 반환 → 없으면 최우선 처리
응답: 현재가 데이터 (< 50ms)
```

## 🛠️ Smart Data Provider 아키텍처 설계

### 🏗️ **2계층 통합 구조**

```
📱 클라이언트 (차트뷰어, 백테스터, 실거래봇)
    ↓ 단일 API 호출
🧠 Layer 2: Smart Data Provider
    ├─ 요청 분석 및 우선순위 처리
    ├─ 캐시 확인 (SQLite + 메모리)
    ├─ 자동 분할 (대용량 요청)
    ├─ 응답 병합 및 형식 통일
    └─ 성능 모니터링
    ↓
💾 Layer 1: Storage & Routing
    ├─ Smart Router V2.0 (기존 완성)
    ├─ SQLite 캔들 스토리지
    ├─ 메모리 실시간 캐시 (TTL)
    └─ Rate Limit 관리
    ↓
🌐 업비트 API (REST/WebSocket)
```

### 📊 **핵심 API 인터페이스 설계**

```python
class SmartDataProvider:
    """통합 마켓 데이터 제공자 - 모든 복잡성을 내부에서 처리"""

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """캔들 데이터 조회 - SQLite 캐시 우선, 자동 분할 처리"""

    async def get_tickers(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """현재가 조회 - 메모리 캐시 우선, Smart Router 폴백"""

    async def get_orderbook(
        self,
        symbols: List[str],
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """호가 조회 - 실시간 메모리 캐시 + WebSocket 연동"""

    async def get_trades(
        self,
        symbol: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        priority: Priority = Priority.NORMAL
    ) -> DataResponse:
        """체결 조회 - 실시간 + 히스토리 데이터 통합"""

# 우선순위 열거형
class Priority(Enum):
    CRITICAL = 1    # 실거래봇 (< 50ms)
    HIGH = 2        # 실시간 모니터링 (< 100ms)
    NORMAL = 3      # 차트뷰어 (< 500ms)
    LOW = 4         # 백테스터 (백그라운드)

# 통합 응답 구조
@dataclass
class DataResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: ResponseMetadata
    error: Optional[str] = None

@dataclass
class ResponseMetadata:
    priority_used: Priority
    cache_hit: bool
    cache_type: str  # "sqlite", "memory", "api"
    response_time_ms: float
    data_count: int
    split_requests: int  # 분할된 요청 수
    source: str  # "smart_router", "cache", "hybrid"
```

## 🗺️ 체계적 작업 계획 (10일)

### Phase 0: 스키마 개선 (1일) ✅ **완료**
- [x] 0.1 기존 스키마 분석 및 문제점 파악
- [x] 0.2 개별 코인별 개별 타임프레임별 독립 테이블 설계
- [x] 0.3 최적화된 스키마 작성 (optimized_market_data_schema.sql)
- [x] 0.4 동적 캔들 테이블 관리자 구현 (CandleTableManager)
- [x] 0.5 기본 마켓 데이터 초기화 및 테스트

### Phase 1: 핵심 구조 설계 (3일) ✅ **완료**
- [x] 1.1 SmartDataProvider 메인 클래스 구현
- [x] 1.2 Priority 기반 요청 처리 시스템
- [x] 1.3 4개 기본 API 인터페이스 구현
- [x] 1.4 Smart Router V2.0 연동 어댑터

### Phase 2: 스토리지 시스템 통합 (4일) ✅ **100% 완료 & 통합 테스트 성공**
- [x] 2.1 SQLite 캔들 캐시 시스템 구현 ✅ **업비트 API 완전 호환 완료**
- [x] 2.2 메모리 실시간 캐시 (티커/호가/체결) 구현 ✅ **완료 - TTL 기반 0.2~0.4ms 초고속 캐싱**
- [x] 2.3 캐시 조정자 - 적중률 최적화 및 TTL 관리 ✅ **완료 - 스마트 TTL & 프리로딩 & 통계 시스템**
- [x] 2.4 스토리지 성능 모니터링 및 통계 ✅ **완료 - 종합 성능 분석 & 실시간 모니터링**

#### **Phase 2 통합 테스트 결과 (2025-08-22)**
- ✅ 티커 캐시: 0.2~0.4ms 응답속도, TTL=1.0s
- ✅ 호가 캐시: 13~1229ms 응답속도, TTL=4.5s (Rate Limit 포함)
- ✅ 캐시 조정자: 12회 요청 중 25% 적중률, 3개 심볼 추적
- ✅ 성능 모니터: 메모리 0.01MB, 6개 엔트리 관리
- ✅ Smart Router V2.0 완전 통합: WebSocket 연동 성공
- ⚠️ 체결 데이터: Smart Router에서 미구현 (Phase 3에서 보완 예정)

### Phase 3: 자동화 기능 (2일) ✅ **완료 - 부분적 문제 발견**
- [x] 3.1 대용량 요청 자동 분할 시스템 ✅ **완료 - RequestSplitter 273줄 구현완료**
- [x] 3.2 분할된 응답 자동 병합 시스템 ✅ **완료 - ResponseMerger 완전구현**
- [x] 3.3 우선순위별 큐 관리 및 부하 제어 ✅ **완료 - PriorityQueueManager 406줄 구현완료**
- [x] 3.4 백그라운드 진행률 추적 시스템 ✅ **완료 - BackgroundProcessor 534줄 구현완료**

#### **Phase 3 검증 결과 (2025-08-22 17:43)**
**✅ 정상 동작 확인:**
- 모든 캔들 요청 방식 성공 (개수 기반, 시간 범위, 우선순위)
- RequestSplitter 분할 로직 정상 (300개→분할 필요, 50개→분할 불필요)
- Smart Router 로깅 불일치 문제 해결 (캔들 개수 올바른 표시)
- 데이터베이스 저장 정상 (기존 심볼)

**⚠️ 발견된 문제들:**
- **오류 처리 미흡**: 존재하지 않는 심볼도 success=True 반환
- **FOREIGN KEY 제약**: 새로운 심볼 저장 시 market_symbols 테이블 의존성 문제
- **캐시 검증 한계**: 기존 캐시된 데이터로 인한 캐시 미스→히트 패턴 확인 불가
- **🚨 DDD 아키텍처 위반**: CandleTableManager가 잘못된 위치에서 직접 sqlite3 사용

**📊 객관적 검증 메트릭:**
- 모든 요청 성공: ✅ True
- RequestSplitter 동작: ✅ True
- 캐시 시스템 동작: ❌ False (검증 시나리오 문제)
- 오류 처리 동작: ❌ False (잘못된 심볼 처리 부적절)
- **DDD 아키텍처 준수**: ❌ False (CandleTableManager 위치 및 구현 위반)
- **전체 시스템 상태**: ❌ **긴급 수정 필요** (아키텍처 위반)

### Phase 4: 통합 테스트 및 최적화 (1일) ✅ **95% 완료 - 소규모 개선사항 남음**
- [x] 4.1 클라이언트별 시나리오 테스트 ✅ **완료 - 우선순위별 성능 검증 완료**
- [x] 4.2 성능 벤치마크 및 캐시 효율성 검증 ✅ **완료 - 캐시 시스템 검증 완료**
- [x] 4.3 기존 시스템 호환성 어댑터 ✅ **완료 - SmartRouterAdapter 구현**
- [-] 4.4 모니터링 대시보드 및 경고 시스템 ⚠️ **90% 완료 - 성능 모니터 구현, 대시보드 UI 개선 필요**

### ✅ Phase 4.5: **DDD 아키텍처 수정** (1일) ✅ **100% 완료**

#### **✅ 완료된 DDD 아키텍처 수정사항**
- ✅ **CandleTableManager → SqliteCandleRepository**: Repository 패턴 완전 구현
- ✅ **DatabaseManager 통합**: 하드코딩 제거, 설정 기반 경로 사용
- ✅ **Repository 인터페이스**: CandleRepositoryInterface 정의 및 의존성 주입
- ✅ **FOREIGN KEY 해결**: ensure_symbol_exists() 자동 심볼 등록 기능
- ✅ **Smart Data Provider 의존성**: Repository 인터페이스 기반 DDD 준수

#### **4.5.1 CandleTableManager → SqliteCandleRepository 리팩터링** ❌ **즉시 필요**
**목표**: DDD Repository 패턴 준수 및 DatabaseManager 통합
**현재 문제**:
- ❌ 위치: `market_data_backbone/candle_table_manager.py`
- ❌ 직접 sqlite3 사용 (`import sqlite3`, `sqlite3.connect()`)
- ❌ 하드코딩: `"data/market_data.sqlite3"` 경로 하드코딩
- ❌ DDD 위반: Repository 인터페이스 없음, Infrastructure 레이어 혼재

**수정 계획**:
```
✅ 새 위치: infrastructure/repositories/sqlite_candle_repository.py
✅ DatabaseManager 사용: infrastructure/database/database_manager.py 활용
✅ 설정 기반 경로: config에서 DB 경로 주입
✅ Repository 인터페이스: domain/repositories/candle_repository_interface.py 생성
✅ 의존성 주입: Smart Data Provider에서 interface 의존
```

#### **4.5.2 DatabaseManager 통합 및 하드코딩 제거** ❌ **즉시 필요**
**기존 DatabaseManager 활용**:
```python
# 현재 잘못된 구현
def get_connection(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self.db_path)  # ❌ 직접 sqlite3 사용

# ✅ 올바른 구현
def __init__(self, db_manager: DatabaseManager):
    self.db_manager = db_manager

async def get_connection(self):
    return await self.db_manager.get_connection("market_data")
```

#### **4.5.3 Repository 인터페이스 정의 및 의존성 주입** ❌ **즉시 필요**
**Domain Layer Interface**:
```python
# domain/repositories/candle_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class CandleRepositoryInterface(ABC):
    @abstractmethod
    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        pass

    @abstractmethod
    async def insert_candles(self, symbol: str, timeframe: str, candles: List[Dict]) -> int:
        pass

    @abstractmethod
    async def get_candles(self, symbol: str, timeframe: str, **kwargs) -> List[Dict]:
        pass
```

#### **4.5.4 Smart Data Provider → Repository 의존성 변경** ❌ **즉시 필요**
**현재 잘못된 의존성**:
```python
# ❌ 현재 구현
from upbit_auto_trading.infrastructure.market_data_backbone.candle_table_manager import CandleTableManager
self.candle_manager = CandleTableManager(db_path)  # 직접 의존
```

**✅ 올바른 DDD 의존성**:
```python
# ✅ 수정된 구현
from upbit_auto_trading.domain.repositories.candle_repository_interface import CandleRepositoryInterface

def __init__(self, candle_repository: CandleRepositoryInterface):
    self.candle_repository = candle_repository  # Interface 의존
```

**의존성 주입 설정**:
```python
# infrastructure/dependency_injection/container.py
container.register(
    CandleRepositoryInterface,
    SqliteCandleRepository,
    dependencies=[DatabaseManager]
)
```

#### **Phase 4.2 발견된 개선 필요 사항**
**🔧 즉시 수정 필요:**
1. **오류 처리 개선**
   - 문제: 존재하지 않는 심볼도 success=True 반환
   - 해결: Smart Data Provider에서 적절한 실패 응답 구현

2. **FOREIGN KEY 제약 해결**
   - 문제: 새로운 심볼 저장 시 market_symbols 의존성 실패
   - 해결: SqliteCandleRepository에서 새로운 심볼 자동 등록 기능 구현

3. **캐시 검증 시나리오 개선**
   - 문제: 기존 캐시된 데이터로 인한 테스트 한계
   - 해결: 새로운 심볼이나 캐시 클리어 후 테스트 시나리오 구성

#### **🚨 Phase 4.5 발견된 중대한 DDD 아키텍처 위반**
**❌ CandleTableManager 위치 및 구현 문제:**
1. **위치 위반**: `market_data_backbone/candle_table_manager.py` (❌) → `infrastructure/repositories/sqlite_candle_repository.py` (✅)
2. **직접 sqlite3 사용**: Repository 패턴 무시, DatabaseManager 무시
3. **하드코딩**: `"data/market_data.sqlite3"` 경로 하드코딩
4. **계층 위반**: Infrastructure에서 직접 DB 접근, 비즈니스 로직 혼재
5. **의존성 역전 위반**: Repository 인터페이스 없음, 의존성 주입 없음

**📊 아키텍처 위반 영향도:**
- Smart Data Provider 전체 시스템이 잘못된 구조에 의존
- 테스트 불가능, 설정 변경 불가능, DDD 원칙 완전 위반
- **긴급 리팩터링 필수**: 전체 시스템 안정성에 직접적 영향

**📝 개선 우선순위:**
- **Priority 0**: **DDD 아키텍처 준수** (CandleTableManager → SqliteCandleRepository 리팩터링)
- **Priority 1**: FOREIGN KEY 제약 해결 (신규 심볼 자동 등록)
- **Priority 2**: 오류 처리 개선 (존재하지 않는 심볼 적절한 실패)
- **Priority 3**: 캐시 검증 시나리오 재설계

## 🛠️ 실제 구현된 파일 구조 (2025-08-22 기준)

```
smart_data_provider/                   # 통합 데이터 제공자
├── core/                              # 핵심 구현 ✅ 구현완료
│   └── smart_data_provider.py         # 메인 제공자 클래스 (733줄)
├── cache/                             # 캐시 시스템 ✅ 구현완료
│   ├── memory_realtime_cache.py       # 메모리 실시간 캐시 (TTL 기반)
│   ├── cache_coordinator.py           # 캐시 조정자 (스마트 TTL & 통계)
│   └── storage_performance_monitor.py # 스토리지 성능 모니터링
├── processing/                        # 요청 처리 ✅ 구현완료
│   ├── request_splitter.py            # 대용량 요청 분할 (273줄)
│   ├── response_merger.py             # 응답 병합
│   ├── priority_queue.py              # 우선순위 큐 관리 (406줄)
│   └── background_processor.py        # 백그라운드 처리 (534줄)
├── adapters/                          # 외부 연동 ✅ 구현완료
│   └── smart_router_adapter.py        # Smart Router V2.0 연동 (343줄)
└── models/                            # 데이터 모델 ✅ 구현완료
    ├── requests.py                    # 요청 모델
    ├── responses.py                   # 응답 모델
    ├── priority.py                    # 우선순위 열거형
    └── cache_models.py                # 캐시 데이터 모델
```

**❌ 문서와 다른 부분:**
- `utils/` 폴더 없음 (계획되었으나 미구현)
- `request_processor.py`, `response_builder.py` 등 일부 파일 미구현
- `sqlite_candle_cache.py` 대신 CandleTableManager가 별도 위치에 구현됨
- `database_adapter.py`, `legacy_client_adapter.py` 미구현

## 🎯 핵심 구현 전략

### 1. **기존 자산 100% 활용**
```python
class SmartDataProvider:
    def __init__(self):
        # 기존 완성된 시스템 활용
        self.smart_router = get_smart_router()  # Smart Router V2.0
        self.db_manager = DatabaseManager()     # 기존 DB 매니저

        # 새로 추가되는 캐시 시스템
        self.candle_cache = SQLiteCandleCache()
        self.realtime_cache = MemoryRealtimeCache(ttl=60)
        self.priority_queue = PriorityQueue()
```

### 2. **스마트 캐시 전략**
```python
async def get_candles(self, symbol: str, timeframe: str, count: int):
    # 1. SQLite 캐시 확인
    cached = await self.candle_cache.get(symbol, timeframe, count)
    if cached.is_complete():
        return self._build_response(cached.data, cache_hit=True, cache_type="sqlite")

    # 2. 부족한 부분만 Smart Router로 요청
    missing_ranges = cached.get_missing_ranges(count)
    if missing_ranges:
        for range_req in missing_ranges:
            fresh_data = await self.smart_router.get_candles(symbol, timeframe, range_req)
            await self.candle_cache.store(fresh_data)

    # 3. 완전한 데이터 반환
    complete_data = await self.candle_cache.get(symbol, timeframe, count)
    return self._build_response(complete_data, cache_hit="hybrid", cache_type="sqlite+api")
```

### 3. **자동 분할 및 병합**
```python
async def _handle_large_request(self, symbol: str, timeframe: str, count: int):
    if count <= 200:  # 업비트 API 한계
        return await self._single_request(symbol, timeframe, count)

    # 자동 분할 (200개씩)
    chunks = self.splitter.split_candle_request(symbol, timeframe, count)
    logger.info(f"대용량 요청 분할: {count}개 → {len(chunks)}개 청크")

    # 병렬 처리
    tasks = [self._process_chunk(chunk) for chunk in chunks]
    chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 자동 병합
    merged_result = self.merger.merge_candle_results(chunk_results)
    return self._build_response(merged_result, split_requests=len(chunks))
```

### 4. **우선순위 기반 처리**
```python
async def _process_with_priority(self, request: DataRequest):
    if request.priority == Priority.CRITICAL:
        # 실거래봇: 즉시 처리, 캐시 우선
        return await self._critical_path(request)

    elif request.priority == Priority.LOW:
        # 백테스터: 백그라운드 큐에 등록
        return await self._background_queue.add(request)

    else:
        # 일반: 표준 경로
        return await self._standard_path(request)
```

## 🔗 우선순위별 처리 흐름 상세

### **CRITICAL 경로 (실거래봇)**
```
🤖 실거래봇 요청
    ↓ priority=CRITICAL 확인
🧠 Smart Data Provider
    ├─ 메모리 캐시 확인 (< 1초 데이터면 즉시 반환)
    ├─ 캐시 없으면 Smart Router 최우선 처리
    └─ 응답 시간 < 50ms 보장
    ↓
🤖 실거래봇 (즉시 매매 신호 판단)
```

### **NORMAL 경로 (차트뷰어)**
```
🖥️ 차트뷰어 요청 (1000개 캔들)
    ↓ 대용량 요청 감지
🧠 Smart Data Provider
    ├─ SQLite 캐시 확인 (기존 데이터 최대한 활용)
    ├─ 부족한 부분만 자동 분할 (5번의 200개 요청)
    ├─ Smart Router 병렬 처리
    ├─ SQLite 자동 저장
    └─ 완전한 데이터 병합하여 응답
    ↓
🖥️ 차트뷰어 (< 2초 내 1000개 캔들 렌더링)
```

### **LOW 경로 (백테스터)**
```
📈 백테스터 요청 (3개월 데이터)
    ↓ priority=LOW 확인
🧠 Smart Data Provider
    ├─ SQLite 우선 조회 (기존 데이터 최대한 활용)
    ├─ 부족한 구간 식별 및 백그라운드 큐 등록
    ├─ 시스템 부하 확인 후 순차 처리
    ├─ 진행률 추적 및 피드백
    └─ 완료된 구간부터 점진적 제공
    ↓
📈 백테스터 (완료된 구간부터 순차 시뮬레이션)
```

## 🎯 성공 기준

### 기능적 성공 기준
- ✅ **4개 API**: 캔들/티커/호가/체결 API 완벽 동작
- ✅ **자동 캐시**: SQLite + 메모리 이중 캐시로 95% 이상 적중률
- ✅ **자동 분할**: 대용량 요청 자동 처리, 클라이언트 인식 불가
- ✅ **우선순위**: CRITICAL < 50ms, LOW는 백그라운드 처리

### 성능적 성공 기준
- ✅ **캐시 적중률**: SQLite 90% 이상, 메모리 80% 이상
- ✅ **응답 시간**: CRITICAL < 50ms, NORMAL < 500ms
- ✅ **처리량**: 동시 100개 요청 처리 가능
- ✅ **메모리 효율성**: 실시간 캐시 100MB 이하 유지

### 운영적 성공 기준
- ✅ **API 호출 절약**: 기존 대비 70% 이상 API 호출 감소
- ✅ **DB 효율성**: SQLite 캔들 데이터 중복률 5% 이하
- ✅ **장애 대응**: Smart Router 장애 시 자동 폴백
- ✅ **모니터링**: 실시간 성능 지표 및 캐시 통계

## 💡 작업 시 주의사항

### Smart Router V2.0 연동 원칙
- **완전 활용**: 기존 33개 테스트 통과한 안정적 시스템 그대로 사용
- **어댑터 패턴**: SmartRouterAdapter로 인터페이스 통일
- **성능 보장**: Smart Router의 채널 선택 로직 100% 활용
- **장애 대응**: Smart Router의 폴백 메커니즘 그대로 상속

### 캐시 시스템 원칙
- **SQLite 우선**: 캔들 데이터는 반드시 SQLite에 영구 저장
- **메모리 보조**: 실시간 데이터만 메모리 캐시 (TTL 관리)
- **스마트 갱신**: 오래된 캐시는 백그라운드에서 자동 갱신
- **용량 관리**: SQLite 자동 정리, 메모리 LRU 정책

### 성능 최적화 원칙
- **분할 최적화**: 업비트 API 제한(200개)에 맞춘 자동 분할
- **병렬 처리**: asyncio.gather로 동시 요청 최대화
- **우선순위 보장**: 실거래 요청은 절대 지연 없음
- **진행률 피드백**: 대용량 요청시 실시간 진행 상황 제공

## 🚀 즉시 시작할 작업

### 1. 기존 시스템 인터페이스 분석
```powershell
# Smart Router V2.0 API 확인
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\smart_routing -Include "*.py" -Recurse

# 기존 클라이언트 사용 패턴 분석
python -c "
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.main_system_adapter import get_market_data_adapter
adapter = get_market_data_adapter()
print('현재 어댑터 상태:', adapter.get_performance_summary())
"
```

### 2. SQLite 캐시 테이블 설계
```sql
-- 캔들 캐시 테이블 (market_data.sqlite3)
CREATE TABLE candle_cache (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    open_price DECIMAL(20,8),
    high_price DECIMAL(20,8),
    low_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    volume DECIMAL(20,8),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, timeframe, timestamp)
);

CREATE INDEX idx_candle_cache_lookup ON candle_cache(symbol, timeframe, timestamp);
```

### 3. 메모리 캐시 구조 설계
```python
# 실시간 데이터 메모리 캐시
class MemoryRealtimeCache:
    def __init__(self, ttl: int = 60):
        self.ticker_cache = TTLCache(maxsize=500, ttl=ttl)      # 현재가
        self.orderbook_cache = TTLCache(maxsize=200, ttl=10)    # 호가 (짧은 TTL)
        self.trades_cache = TTLCache(maxsize=100, ttl=30)       # 체결
```

## 📋 관련 문서 및 리소스

### 핵심 참고 자료
- **Smart Router V2.0**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
- **기존 어댑터**: `smart_routing/main_system_adapter.py`
- **DB 스키마**: `data_info/upbit_autotrading_schema_market_data.sql`

### 설계 참고 문서
- **기존 시스템 분석**: `docs/업비트 마켓 데이터 통합 API 구현 평가 및 방안.md`
- **Smart Router 기획**: `docs/UPBIT_SMART_ROUTER_V2_PLAN.md`

## 🔄 태스크 연관성

### 기반 태스크
- **Smart Router V2.0**: ✅ 완료 (33개 테스트 통과)
- **DB 스키마**: ✅ 완료 (SQLite 구조 준비)

### 후속 태스크
- **클라이언트 마이그레이션**: 기존 시스템을 Smart Data Provider로 전환
- **성능 튜닝**: 운영 환경에서의 캐시 최적화

---

## 📊 **예상 소요 시간**

### 🔥 **단계별 작업 일정**
1. **Phase 1 - 핵심 구조**: 3일
2. **Phase 2 - 스토리지 통합**: 4일
3. **Phase 3 - 자동화 기능**: 2일
4. **Phase 4 - 통합 테스트**: 1일

### 📈 **총 예상 소요 시간**: 10일

---

**시작 조건**: Smart Router V2.0 완료, SQLite 스키마 준비
**핵심 가치**: DB 효율적 보관 + 자동 캐시 + 투명한 복잡성 + Smart Router 활용
**성공 지표**: 캐시 적중률 + API 호출 절약 + 응답 속도 + 시스템 안정성

**🎯 최종 목표**: 마켓 데이터가 DB에 잘 보관되어 모든 클라이언트에게 효율적으로 제공되는 완벽한 통합 시스템!

**🌟 원래 목표 달성**: 이 태스크 완료 시 DB 기반 효율적 마켓 데이터 제공 시스템 완성!
