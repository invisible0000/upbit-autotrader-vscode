# MarketDataBackbone V2 진화적 개발 전략

## 🎯 **현재 상황 분석**

### **코드 규모 현황 (800라인 기준 위험도)**
```
unified_market_data_api.py: 476라인 (⚠️ 위험)
data_unifier.py: 492라인 (⚠️ 위험)
websocket_manager.py: 348라인 (안전)
market_data_backbone.py: 347라인 (안전)
channel_router.py: 141라인 (안전)

위험 파일: 2개
안전 파일: 3개
총 라인수: 1,804라인 (평균 361라인/파일)
```

### **800라인 초과 시 강제 분리 대상**
- `unified_market_data_api.py` (476 → 800라인 접근 중)
- `data_unifier.py` (492 → 800라인 접근 중)

---

## 🏗️ **MarketDataBackbone 3대 핵심 기능**

### **1. 데이터 수집 기능 (Data Collection Engine)**
```yaml
책임:
  - 업비트 API 호출 관리
  - Rate Limit 및 에러 처리
  - 실시간 WebSocket 관리
  - 백그라운드 데이터 수집

현재 위치: unified_market_data_api.py (일부)
진화 방향: DataCollectionEngine 독립 모듈
```

### **2. 데이터 저장/관리 기능 (Data Storage Manager)**
```yaml
책임:
  - SQLite DB 효율적 저장
  - 캐시 관리 및 TTL 처리
  - 중복 제거 및 무결성 보장
  - 데이터 압축 및 아카이빙

현재 위치: data_unifier.py (일부)
진화 방향: DataStorageManager 독립 모듈
```

### **3. 데이터 제공 기능 (Data Service Provider)**
```yaml
책임:
  - 포지션별 맞춤 데이터 제공
  - 지능형 캐시 활용
  - 실시간성 vs 신뢰성 최적화
  - 성능 모니터링 및 최적화

현재 위치: unified_market_data_api.py (일부)
진화 방향: DataServiceProvider 독립 모듈
```

---

## 🔄 **진화적 개발 로드맵**

### **Phase 1: 현재 (통합 모듈)**
```
unified_market_data_api.py (476라인)
├── SmartChannelRouter
├── DataCollectionLogic
├── DataServiceLogic
└── ErrorHandling

data_unifier.py (492라인)
├── DataNormalization
├── CacheManagement
├── DataValidation
└── PerformanceOptimization
```

### **Phase 2: 기능 분리 (800라인 초과 시)**
```
data_collection/
├── api_client.py (200라인)
├── websocket_client.py (200라인)
├── rate_limiter.py (150라인)
└── collection_scheduler.py (200라인)

data_storage/
├── db_manager.py (200라인)
├── cache_manager.py (200라인)
├── data_validator.py (150라인)
└── archiver.py (150라인)

data_service/
├── service_provider.py (200라인)
├── query_optimizer.py (150라인)
├── performance_monitor.py (150라인)
└── adaptive_strategy.py (200라인)
```

### **Phase 3: 최적화된 마이크로 서비스**
```
각 모듈 200라인 이하 유지
독립적 테스트 가능
명확한 인터페이스 정의
LLM 친화적 코드 구조
```

---

## 🧪 **테스트 중심 진화 전략**

### **테스트가 진화의 안전망 역할**
```python
# 현재 테스트 구조
tests/
├── sc01_basic_api_response.py
├── sc07_candle_storage.py
├── sc08_fragmented_requests.py
├── sc09_overlapping_requests.py
├── sc10_websocket_integration.py
├── sc11_strategic_data_collection.py
└── sc12_realworld_trading_patterns.py

# 진화 후 테스트 구조
tests/
├── data_collection/
│   ├── test_api_client.py
│   ├── test_websocket_client.py
│   └── test_rate_limiter.py
├── data_storage/
│   ├── test_db_manager.py
│   ├── test_cache_manager.py
│   └── test_data_validator.py
└── data_service/
    ├── test_service_provider.py
    ├── test_query_optimizer.py
    └── test_adaptive_strategy.py
```

### **과감한 코드 교체 원칙**
```yaml
교체 조건:
  - 800라인 초과
  - 성능 병목 발견
  - 새로운 요구사항 등장
  - 테스트 커버리지 부족

교체 방법:
  1. 기존 테스트 수행 (회귀 방지)
  2. 새 모듈 개발 (테스트 우선)
  3. 점진적 교체 (A/B 테스트)
  4. 기존 코드 삭제 (과감한 정리)
```

---

## 🔍 **포지션 연동 최적화**

### **포지션에서 요구 데이터 사전 예측**
```python
# 포지션 → MarketDataBackbone 요청 예시
class PositionDataRequirements:
    """포지션별 데이터 요구사항 사전 정의"""

    def __init__(self, strategy_config: dict):
        self.required_indicators = self._extract_indicators(strategy_config)
        self.update_frequencies = self._calculate_frequencies(strategy_config)
        self.priority_levels = self._assign_priorities(strategy_config)

    def get_data_plan(self) -> DataCollectionPlan:
        """데이터 수집 계획 생성"""
        return DataCollectionPlan(
            indicators=self.required_indicators,
            frequencies=self.update_frequencies,
            priorities=self.priority_levels,
            prefetch_strategy="adaptive"
        )

# MarketDataBackbone 응답 최적화
class DataServiceProvider:
    """효율적 데이터 제공 서비스"""

    async def register_position_requirements(self, position_id: str,
                                           requirements: PositionDataRequirements):
        """포지션 요구사항 등록 및 사전 준비"""

        # 1. 요구사항 분석
        plan = requirements.get_data_plan()

        # 2. 사전 데이터 준비
        await self._prefetch_data(plan)

        # 3. 실시간 업데이트 스케줄링
        await self._schedule_updates(position_id, plan)

    async def get_position_data(self, position_id: str,
                              data_request: DataRequest) -> DataResponse:
        """포지션별 최적화된 데이터 제공"""

        # 캐시 우선 확인
        cached_data = await self.cache_manager.get_position_cache(position_id)

        if self._is_sufficient(cached_data, data_request):
            return self._format_response(cached_data)

        # 최소 필요량만 추가 수집
        additional_data = await self._collect_minimal_update(data_request)

        # 캐시 업데이트
        await self.cache_manager.update_position_cache(position_id, additional_data)

        return self._format_response(cached_data + additional_data)
```

---

## 📊 **800라인 분리 시나리오**

### **분리 트리거 조건**
```python
def should_split_module(module_path: str) -> bool:
    """모듈 분리 필요성 판단"""

    line_count = count_lines(module_path)
    complexity = calculate_complexity(module_path)
    test_coverage = get_test_coverage(module_path)

    return (
        line_count > 800 or
        complexity > 15 or
        test_coverage < 0.8
    )

# 자동 분리 실행
if should_split_module("unified_market_data_api.py"):
    split_strategy = analyze_split_strategy(module)
    new_modules = execute_split(module, split_strategy)

    # 테스트 마이그레이션
    migrate_tests(original_tests, new_modules)

    # 회귀 테스트
    assert run_regression_tests() == "PASS"

    # 기존 파일 삭제
    remove_legacy_file("unified_market_data_api.py")
```

### **분리 후 예상 구조**
```
market_data_backbone_v3/
├── collection/
│   ├── api_collector.py (180라인)
│   ├── websocket_collector.py (200라인)
│   └── rate_manager.py (120라인)
├── storage/
│   ├── db_engine.py (200라인)
│   ├── cache_engine.py (180라인)
│   └── validator.py (100라인)
├── service/
│   ├── data_provider.py (200라인)
│   ├── query_optimizer.py (150라인)
│   └── adaptive_engine.py (180라인)
└── coordinator.py (100라인) # 전체 조정
```

---

## 🎯 **핵심 성공 요소**

### **1. 테스트 무결성 보장**
- 모든 변경 전 테스트 수행
- 새 모듈은 테스트 우선 개발
- 회귀 테스트 자동화

### **2. 점진적 진화**
- 한 번에 전체 교체 금지
- A/B 테스트로 안전성 확보
- 성능 지표 지속 모니터링

### **3. LLM 친화적 구조**
- 각 파일 200-300라인 유지
- 명확한 책임 분리
- 간결한 인터페이스 정의

### **4. 과감한 삭제 문화**
- 레거시 코드 과감한 제거
- 기능 중복 즉시 통합
- 불필요한 복잡성 제거

---

## 🚀 **결론**

**MarketDataBackbone은 살아있는 시스템**입니다. 800라인 기준으로 과감하게 분리하고, 테스트를 안전망으로 활용하여 지속적으로 진화시켜야 합니다.

**핵심 원칙**:
1. **테스트 우선** - 모든 변경은 테스트가 보장
2. **기능 분리** - 800라인 초과 시 강제 분리
3. **과감한 교체** - 레거시 코드 즉시 제거
4. **LLM 친화** - 200-300라인 모듈 유지

이렇게 진화하면 **포지션 관리와의 완벽한 연동**과 **극도로 효율적인 데이터 제공**이 가능할 것입니다! 🎯
