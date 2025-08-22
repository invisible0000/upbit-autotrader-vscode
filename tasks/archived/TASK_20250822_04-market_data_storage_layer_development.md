# 📋 TASK_20250822_04: Market Data Storage Layer 개발

## 🎯 태스크 목표
- **주요 목표**: 완성된 Smart Routing V2.0과 연동되는 Market Data Storage Layer (Layer 2) 구현
- **완료 기준**:
  - ✅ 캔들 데이터 영속성 보장 (SQLite DB 저장)
  - ✅ 실시간 데이터 메모리 캐시 (티커/호가창/체결)
  - ✅ Smart Router 캐시와 협력하여 중복 방지
  - ✅ Layer 1과 완벽 연동되는 Storage API

## 📊 현재 상황 분석 (2025-08-22 기준)

### ✅ **Layer 1: Smart Routing V2.0 완료 상황**
- **33개 테스트 100% 통과**: 스마트 라우팅 시스템 완전 검증 완료
- **실제 업비트 API 연동**: REST/WebSocket 클라이언트 정상 동작
- **실시간 메모리 캐시**: 5-30분 TTL 캐시 시스템 ✅
- **데이터 형식 통일**: `DataFormatUnifier`로 REST/WebSocket 응답 통일
- **표준 응답 구조**: `{'success': bool, 'data': dict, 'metadata': dict}` 확립

### 🎯 **Layer 2: Storage의 역할 정의**

#### **핵심 책임**
- **선택적 영속성**: 캔들 데이터만 SQLite DB 저장, 실시간 데이터는 메모리 캐시만
- **Layer 1 연동**: Smart Router 캐시와 협력하여 중복 캐싱 방지
- **계층적 캐시**: Storage 메모리 → Storage 디스크 → SQLite DB
- **데이터 정합성**: 타임스탬프 기반 중복 검사, 연속성 검증

#### **데이터 저장 전략**
```
캔들 데이터 (OHLCV) → 완전 영속성
├─ Layer 1 캐시: 최근 200개 (5분 TTL)
├─ Layer 2 메모리: 최근 1000개 (1시간 TTL)
├─ Layer 2 디스크: 최근 1개월 (1일 TTL)
└─ SQLite DB: 전체 히스토리 (영구 저장)

실시간 데이터 (티커/호가창/체결) → 메모리 캐시만
├─ Layer 1 캐시: 실시간 데이터 (5-30분 TTL)
├─ Layer 2 메모리: 히스토리 (30분-1시간 TTL)
└─ DB 저장 없음 (메모리 효율성 우선)
```

## 🛠️ Storage Layer 아키텍처 설계

### 🔗 **Layer 1과의 연동 흐름**

```
클라이언트 → Storage Layer API
    ↓
Storage Service (Layer 2)
    ├─ 1차: Layer 1 캐시 확인
    ├─ 2차: Storage 메모리 캐시 확인
    ├─ 3차: Storage 디스크 캐시 확인
    └─ 4차: SQLite DB 조회 (캔들만)
    ↓
데이터 없으면 → Layer 1 Smart Router 요청
    ↓
받은 데이터 → 모든 캐시 레벨 갱신
```

### 📊 **핵심 인터페이스 설계**

```python
# 표준 Storage 요청/응답 구조
@dataclass
class StorageRequest:
    data_type: DataType  # CANDLE, TICKER, ORDERBOOK, TRADE
    symbols: List[str]
    timeframe: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    count: Optional[int] = None

@dataclass
class StorageResponse:
    success: bool
    data: List[Dict[str, Any]]
    metadata: StorageMetadata
    error: Optional[str] = None

@dataclass
class StorageMetadata:
    source: str  # "layer1_cache", "storage_memory", "storage_disk", "sqlite_db"
    cache_hit: bool
    processing_time_ms: float
    data_count: int
```

## 🗺️ 체계적 작업 계획

### Phase 1: 핵심 인터페이스 및 연동 설계 📝 **즉시 시작 가능**
- [ ] 1.1 IMarketDataStorage 인터페이스 정의
- [ ] 1.2 Layer 1 Smart Router 연동 인터페이스 설계
- [ ] 1.3 표준 요청/응답 모델 설계 (StorageRequest/Response)
- [ ] 1.4 캐시 정책 및 TTL 전략 설계

### Phase 2: 캔들 데이터 영속성 시스템 구현
- [ ] 2.1 SQLite 기반 CandleRepository 구현
- [ ] 2.2 캔들 데이터 테이블 스키마 최적화 (인덱스, 파편화 관리)
- [ ] 2.3 배치 저장 및 UPSERT 로직 구현
- [ ] 2.4 데이터 정합성 검증 (중복 검사, 연속성 확인)

### Phase 3: 계층적 캐시 시스템 구현
- [ ] 3.1 Storage 메모리 캐시 구현 (LRU, TTL 정책)
- [ ] 3.2 Storage 디스크 캐시 구현 (압축, 임시 파일)
- [ ] 3.3 Layer 1 캐시 연동 (SmartRouterConnector)
- [ ] 3.4 캐시 간 데이터 동기화 및 일관성 보장

### Phase 4: Storage Service 통합 구현
- [ ] 4.1 MarketDataStorageService 메인 서비스 구현
- [ ] 4.2 데이터 타입별 처리 로직 (캔들/티커/호가창/체결)
- [ ] 4.3 에러 처리 및 폴백 메커니즘
- [ ] 4.4 성능 메트릭 수집 및 모니터링

### Phase 5: 테스트 및 최적화
- [ ] 5.1 Layer 1 연동 테스트
- [ ] 5.2 캔들 데이터 영속성 테스트
- [ ] 5.3 캐시 효율성 및 성능 테스트
- [ ] 5.4 SQLite 최적화 (VACUUM, 인덱스 재구성)

## 🛠️ 단순화된 파일 구조

```
market_data_storage/                   # Layer 2 - Storage
├── __init__.py
├── interfaces/                        # 추상 인터페이스
│   ├── __init__.py
│   ├── storage_service.py            # IMarketDataStorage
│   ├── cache_layer.py                # ICacheLayer
│   └── repository.py                 # IRepository
├── implementations/                   # 핵심 구현체
│   ├── __init__.py
│   ├── storage_service.py            # MarketDataStorageService (메인)
│   ├── candle_repository.py          # 캔들 데이터 SQLite 저장소
│   ├── realtime_cache.py             # 실시간 데이터 메모리 캐시
│   └── smart_router_connector.py     # Layer 1 연동
├── cache/                             # 캐시 시스템
│   ├── __init__.py
│   ├── memory_cache.py               # Storage 메모리 캐시
│   ├── disk_cache.py                 # Storage 디스크 캐시
│   └── cache_policies.py             # TTL, LRU 정책
├── persistence/                       # DB 영속성
│   ├── __init__.py
│   ├── sqlite_manager.py             # SQLite 연결 관리
│   ├── schema_manager.py             # 스키마 및 마이그레이션
│   └── optimization.py               # DB 최적화 (VACUUM, 인덱스)
├── models/                            # 데이터 모델
│   ├── __init__.py
│   ├── storage_request.py            # StorageRequest 모델
│   ├── storage_response.py           # StorageResponse 모델
│   └── cache_entry.py                # 캐시 엔트리 모델
└── utils/                             # 유틸리티
    ├── __init__.py
    ├── data_validator.py             # 데이터 검증
    ├── time_utils.py                 # 시간 관련 유틸리티
    └── performance_monitor.py        # 성능 모니터링
```

## 🎯 핵심 구현 목표

### 1. **Layer 1 Smart Router와의 완벽 연동**
- **캐시 협력**: Layer 1 캐시 우선 활용, Storage는 보조 역할
- **중복 방지**: 동일 데이터 중복 캐싱 완전 제거
- **표준 통신**: Smart Router 응답 구조와 100% 호환
- **성능 최적화**: 추가 레이어로 인한 지연 최소화

### 2. **선택적 영속성 및 캐시 전략**
- **캔들 데이터**: SQLite DB 완전 영속성 + 계층적 캐시
- **실시간 데이터**: 메모리 캐시만 + 히스토리 관리
- **TTL 정책**: 데이터 타입별 차별화된 만료 정책
- **LRU 관리**: 메모리 효율성을 위한 자동 정리

### 3. **데이터 정합성 및 성능**
- **중복 검사**: 타임스탬프 기반 중복 데이터 방지
- **연속성 검증**: 캔들 데이터 시간 순서 및 누락 확인
- **배치 처리**: 대용량 캔들 데이터 효율적 저장
- **인덱스 최적화**: 빠른 조회를 위한 복합 인덱스

### 4. **SQLite 최적화 및 관리**
- **파편화 관리**: 자동 VACUUM 스케줄링
- **인덱스 최적화**: 사용 패턴 기반 인덱스 재구성
- **통계 업데이트**: ANALYZE 자동 실행
- **압축 저장**: 오래된 데이터 선택적 압축

## 🔗 Layer 1 연동 상세 설계

### **SmartRouterConnector 핵심 기능**
```python
class SmartRouterConnector:
    """Layer 1 Smart Router와의 연동을 담당"""

    async def get_from_layer1_cache(self, request: StorageRequest) -> Optional[dict]:
        """Layer 1 캐시에서 데이터 조회"""

    async def request_data_from_layer1(self, request: StorageRequest) -> dict:
        """Layer 1에 새 데이터 요청 (캐시 미스 시)"""

    async def sync_cache_policies(self) -> None:
        """Layer 1과 Storage 간 캐시 정책 동기화"""

    async def monitor_layer1_performance(self) -> dict:
        """Layer 1 성능 지표 모니터링"""
```

### **데이터 요청 흐름**
```
Storage API 호출
    ↓
1차: Layer 1 캐시 확인 (SmartRouterConnector)
    ├─ HIT: 즉시 반환
    └─ MISS: 2차 확인
    ↓
2차: Storage 메모리 캐시 확인
    ├─ HIT: 반환 + Layer 1 캐시 갱신
    └─ MISS: 3차 확인
    ↓
3차: Storage 디스크 캐시 확인 (캔들만)
    ├─ HIT: 반환 + 상위 캐시 갱신
    └─ MISS: 4차 확인
    ↓
4차: SQLite DB 조회 (캔들만)
    ├─ HIT: 반환 + 모든 캐시 갱신
    └─ MISS: Layer 1에 새 데이터 요청
    ↓
Layer 1 Smart Router → 업비트 API 호출
    ↓
새 데이터 수신 → 모든 캐시 레벨 저장
```

## 🎯 성공 기준

### 기능적 성공 기준
- ✅ **Layer 1 연동**: Smart Router 캐시를 1차로 100% 활용
- ✅ **캔들 영속성**: 백테스트용 캔들 데이터 안정적 저장/조회
- ✅ **실시간 캐시**: 티커/호가창/체결 데이터 효율적 메모리 관리
- ✅ **데이터 정합성**: 중복 없고 연속성 있는 데이터 보장

### 성능적 성공 기준
- ✅ **캐시 히트율**: 전체 캐시 시스템 히트율 > 85%
- ✅ **응답 시간**: 캐시 응답 < 10ms, DB 조회 < 100ms
- ✅ **메모리 효율**: Layer 1과 중복 없는 캐시로 50% 메모리 절약
- ✅ **DB 성능**: 1000개 캔들 조회 < 100ms

### 운영적 성공 기준
- ✅ **DB 최적화**: 파편화율 < 15%, 자동 VACUUM 정상 동작
- ✅ **캐시 동기화**: Layer 1과 Storage 간 데이터 일관성 보장
- ✅ **에러 복구**: Storage 장애 시 Layer 1 단독 운영 가능
- ✅ **모니터링**: 실시간 성능 메트릭 정상 수집

## 💡 작업 시 주의사항

### Layer 1 연동 원칙
- **Layer 1 우선**: Smart Router 캐시를 항상 1차로 확인
- **중복 방지**: 동일 데이터 중복 저장 완전 제거
- **표준 준수**: Smart Router 응답 구조 100% 호환
- **성능 우선**: 추가 지연 없는 투명한 연동

### 데이터 저장 원칙
- **선택적 영속성**: 캔들만 DB, 실시간은 메모리만
- **효율적 저장**: 배치 UPSERT, 인덱스 최적화
- **정합성 보장**: 타임스탬프 기반 중복/연속성 검증
- **공간 관리**: 자동 압축, 아카이빙, 정리

### 캐시 관리 원칙
- **계층적 구조**: 메모리 → 디스크 → DB 순차 조회
- **TTL 차별화**: 데이터 타입별 적절한 만료 정책
- **LRU 적용**: 메모리 제한 시 오래된 데이터 자동 제거
- **동기화 보장**: 캐시 간 데이터 일관성 유지

## 🚀 즉시 시작할 작업

### 1. Layer 1 Smart Router 분석
```powershell
# Smart Router 캐시 구조 확인
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone\smart_routing -Include "*.py" -Recurse | Select-String -Pattern "cache"

# Smart Router 응답 구조 확인
python -c "
import asyncio
from upbit_auto_trading.infrastructure.market_data_backbone.smart_routing.main_system_adapter import get_ticker
result = asyncio.run(get_ticker(['KRW-BTC']))
print('응답 구조:', result.keys())
print('메타데이터:', result.get('metadata', {}))
"
```

### 2. 기존 DB 스키마 분석
```powershell
# 현재 market_data DB 구조 확인
python tools\super_db_table_viewer.py market_data

# 기존 market_data_backbone 구조 확인
Get-ChildItem upbit_auto_trading\infrastructure\market_data_backbone -Name
```

### 3. Storage 인터페이스 설계 시작
- `interfaces/storage_service.py`: IMarketDataStorage 인터페이스 정의
- `models/storage_request.py`: StorageRequest 모델 설계
- Layer 1 응답 구조와 호환되는 StorageResponse 설계

## 📋 관련 문서 및 리소스

### 핵심 참고 문서
- **Layer 1 완료**: `upbit_auto_trading/infrastructure/market_data_backbone/smart_routing/`
- **기존 Storage**: `upbit_auto_trading/infrastructure/market_data_backbone/`
- **DB 스키마**: `data_info/upbit_autotrading_schema_market_data.sql`

### 테스트 리소스
- **Smart Router 테스트**: `tests/infrastructure/smart_routing_test/`
- **Layer 1 어댑터**: `tests/infrastructure/smart_routing_test/test_main_system_adapter.py`

## 🔄 태스크 연관성

### 완료된 선행 작업 ✅
- **TASK_20250822_01**: Smart Routing V2.0 통합 완료 (100%)
- **TASK_20250822_02**: Smart Routing 완전 검증 완료 (68.8% 성공률, 핵심 기능 정상)

### 후속 태스크 계획
- **TASK_20250822_05**: Market Data Coordinator 개발 (Layer 3)
- **TASK_20250822_06**: Backbone API 개발 (Layer 4)
- **TASK_20250822_07**: 4계층 통합 테스트

---

## 📊 **예상 소요 시간**

### 🔥 **우선순위별 작업**
1. **Phase 1 - 인터페이스 설계**: 0.5일
2. **Phase 2 - 캔들 영속성**: 1.5일
3. **Phase 3 - 계층적 캐시**: 1.5일
4. **Phase 4 - Storage 통합**: 1일
5. **Phase 5 - 테스트 및 최적화**: 0.5일

### 📈 **총 예상 소요 시간**: 5일

---

**시작 조건**: ✅ **즉시 시작 가능** - Layer 1 Smart Routing 완전 준비 완료
**핵심 가치**: Smart Router와 완벽 연동되는 효율적 Storage Layer
**성공 지표**: Layer 1 협력 + 선택적 영속성 + 캐시 효율성 + 데이터 정합성

**🎯 이번 태스크 목표**: Layer 1 기반의 견고한 Storage Layer 구축으로 다음 Layer들의 기반 마련
