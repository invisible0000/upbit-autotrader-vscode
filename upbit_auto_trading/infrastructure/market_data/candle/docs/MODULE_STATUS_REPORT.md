# 📈 Candle Infrastructure 현재 상태 보고서

**보고 일시**: 2025년 9월 22일
**보고 범위**: `upbit_auto_trading/infrastructure/market_data/candle/` 모듈
**보고 목적**: 현재 상태 파악 및 개선 작업 추적

---

## 📊 현재 모듈 구성

### 파일 목록 및 크기

| 파일명 | 라인 수 | 상태 | 주요 역할 |
|--------|---------|------|-----------|
| `candle_models.py` | 1,081줄 | 🟡 비대함 | 모든 데이터 모델 |
| `candle_data_provider.py` | 1,460줄 | 🟡 개선됨 | 캔들 데이터 수집 |
| `candle_collection_monitor.py` | 245줄 | 🟢 신규 | 모니터링 전용 |
| `candle_cache.py` | ?줄 | 🔍 확인 필요 | 캐시 관리 |
| `overlap_analyzer.py` | ?줄 | 🟢 안정적 | 겹침 분석 |
| `empty_candle_detector.py` | ?줄 | 🟢 안정적 | 빈 캔들 처리 |
| `time_utils.py` | ?줄 | 🟢 안정적 | 시간 유틸리티 |

**총 모듈 크기**: 약 3,000줄+ (추정)

---

## ✅ 완료된 개선 작업

### 1. 모니터링 기능 분리 (2025-09-22 완료)

**변경 사항**:
- `CandleDataProvider`에서 모니터링 메서드 4개 제거
- `CandleCollectionMonitor` 클래스 신규 생성
- 단일 책임 원칙 준수

**효과**:
```diff
- CandleDataProvider: 1,632줄 → 1,460줄 (-172줄, -10.5%)
+ candle_collection_monitor.py: 245줄 (신규)
```

**사용법 변화**:
```python
# Before (책임 혼재)
provider = CandleDataProvider(...)
metrics = provider.get_performance_metrics()

# After (책임 분리)
provider = CandleDataProvider(...)
monitor = CandleCollectionMonitor(provider.get_collection_status())
metrics = monitor.get_performance_metrics()
```

---

## 🔍 식별된 문제점들

### 1. CollectionState 설계 문제 (심각도: 높음)

**문제점**:
- 순수 상태와 계산된 값이 섞여 저장됨
- 시간 정보 중복 (`estimated_completion_time` vs `estimated_remaining_seconds`)
- 매번 수동으로 계산된 값 업데이트 필요

**영향도**:
- 코드 복잡성 증가
- 버그 발생 가능성
- 유지보수 어려움

### 2. candle_models.py 파일 비대화 (심각도: 중간)

**문제점**:
```
candle_models.py (1,081줄)
├── 핵심 모델 (CandleData, CandleDataResponse)
├── 요청/응답 모델 (OverlapRequest, TimeChunk 등)
├── 캐시 모델 (CacheKey, CacheEntry, CacheStats)
├── 수집 프로세스 모델 (CollectionState, ChunkInfo 등)
└── 통계 모델 (ProcessingStats)
```

**영향도**:
- 파일 탐색 어려움
- 관련 없는 변경사항이 충돌 가능
- 새 개발자의 이해 부담

### 3. CandleCollectionMonitor 미완성 (심각도: 낮음)

**미완성 부분**:
- `target_end` 정보 부족으로 시간 기반 진행률 계산 불가
- `should_continue_collection` 로직 부재
- 일부 기능이 TODO 상태

---

## 🎯 제안된 개선 계획

### Phase 1: CollectionState v2.0 적용 (우선순위: 높음)

**목표**: 순수 상태와 계산 로직 분리

**변경 사항**:
```python
# 현재 (문제 있는 설계)
@dataclass
class CollectionState:
    avg_chunk_duration: float = 0.0      # 계산된 값을 상태로 저장
    remaining_chunks: int = 0             # 계산된 값을 상태로 저장
    estimated_remaining_seconds: float = 0.0  # 계산된 값을 상태로 저장

# 제안 (개선된 설계)
@dataclass
class CollectionStateV2:
    # 순수 상태만 저장
    total_collected: int = 0
    completed_chunks: List[ChunkInfo] = field(default_factory=list)

    # 계산된 값은 Property로
    @property
    def avg_chunk_duration(self) -> float:
        return self.elapsed_seconds / len(self.completed_chunks) if self.completed_chunks else 0.0
```

**예상 효과**:
- 🎯 일관성: 항상 최신 값 반환
- 🚀 성능: 필요할 때만 계산
- 🔧 단순성: 수동 업데이트 불필요

### Phase 2: 캐시 모델 분리 (우선순위: 중간)

**목표**: 선택적 기능을 별도 파일로 분리

**분리 대상**:
- `CacheKey`, `CacheEntry`, `CacheStats` → `candle_cache_models.py`

**예상 효과**:
- candle_models.py 200줄 단축
- 캐시 기능의 독립성 확보
- 필요시에만 import 가능

### Phase 3: 전체 모델 파일 분할 (우선순위: 낮음)

**목표**: 역할별 파일 분리

**분할 계획**:
```
candle_models.py (1,081줄)
├── candle_core_models.py (300줄) - 핵심 도메인 모델
├── candle_request_models.py (250줄) - 요청/응답 모델
├── candle_cache_models.py (200줄) - 캐시 모델
└── candle_collection_models.py (400줄) - 수집 프로세스 모델
```

---

## 📈 개선 지표 추적

### 코드 품질 지표

#### 현재 상태
- **파일 크기**: CandleDataProvider 1,460줄 (개선됨), candle_models.py 1,081줄 (비대함)
- **클래스 책임**: 일부 개선됨 (모니터링 분리)
- **코드 중복**: 일부 존재 (CollectionState 계산 로직)
- **테스트 커버리지**: 확인 필요

#### 목표 상태
- **파일 크기**: 각 파일 500줄 이하
- **클래스 책임**: 명확한 단일 책임
- **코드 중복**: 최소화
- **테스트 커버리지**: 90% 이상

### 성능 지표

#### 현재 성능 (추정)
- **메모리 사용량**: CollectionState에 불필요한 계산된 값 저장
- **CPU 사용량**: 중복 계산 가능성
- **응답 시간**: 큰 파일로 인한 IDE 응답 지연

#### 목표 성능
- **메모리 사용량**: 20% 절약 (계산된 값 제거)
- **CPU 사용량**: 필요시에만 계산으로 효율화
- **응답 시간**: 파일 분리로 IDE 성능 향상

---

## 🚀 다음 단계 실행 계획

### 즉시 실행 가능 (1-2일)
1. **CollectionState v2.0 프로토타입 구현**
   - 기본 클래스 정의
   - 주요 Property 메서드 구현
   - 간단한 테스트 케이스 작성

2. **캐시 모델 분리**
   - `candle_cache_models.py` 생성
   - 기존 import 구문 업데이트

### 중기 계획 (1주일)
1. **CollectionState v2.0 전면 적용**
   - CandleDataProvider 업데이트
   - 마이그레이션 로직 구현
   - 전체 테스트 실행

2. **CandleCollectionMonitor 완성**
   - 누락된 기능 구현
   - 문서화 완료

### 장기 계획 (2-3주일)
1. **전체 모델 파일 분할**
   - 단계적 분리 실행
   - 의존성 그래프 검증
   - 성능 벤치마크

---

## ⚠️ 리스크 및 대응 방안

### 리스크 1: 하위 호환성 깨짐
**확률**: 중간
**영향**: 높음
**대응 방안**:
- 기존 API 유지하면서 새 API 추가
- Deprecation warning으로 점진적 전환
- 충분한 테스트 케이스로 검증

### 리스크 2: 성능 저하
**확률**: 낮음
**영향**: 중간
**대응 방안**:
- Property 계산 복잡도 최소화
- 필요시 캐싱 메커니즘 적용
- 성능 벤치마크로 사전 검증

### 리스크 3: 개발 일정 지연
**확률**: 중간
**영향**: 낮음
**대응 방안**:
- 단계별 진행으로 리스크 분산
- 우선순위 기반 작업
- 필요시 일부 개선 사항 연기

---

## 📚 관련 문서

- `REFACTORING_ANALYSIS_REPORT.md` - 상세 분석 보고서
- `IMPLEMENTATION_GUIDE.md` - 구체적 구현 가이드
- `temp/collection_state_v2_proposal.py` - CollectionState v2.0 제안서
- `temp/candle_models_refactoring_plan.py` - 파일 분할 계획

---

## 📞 문의 및 피드백

이 상태 보고서에 대한 질문이나 제안사항이 있으시면:

1. **기술적 문의**: IMPLEMENTATION_GUIDE.md 참조
2. **전략적 문의**: REFACTORING_ANALYSIS_REPORT.md 참조
3. **우선순위 조정**: 현재 개발 일정과 비즈니스 요구사항 고려

---

**마지막 업데이트**: 2025년 9월 22일
**다음 리뷰 예정**: CollectionState v2.0 구현 완료 후
