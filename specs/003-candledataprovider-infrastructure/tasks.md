````markdown
# Tasks: OverlapAnalyzer v5.0 Infrastructure 레이어 모델

**Input**: Design documents from `/specs/003-candledataprovider-infrastructure/`
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Summary
Infrastructure 레이어에 업비트 API 완전 호환 스키마와 frozen dataclass 기반 불변 모델 구현.
OverlapAnalyzer v5.0과의 100% 호환성 유지하며 200개 청크 분할 최적화 적용.

**Target Files**: 3 new modules + 7 test files = **10 files total**
**Estimated Time**: 2-3 days (TDD approach)
**Performance Goal**: 기존 대비 성능 유지 또는 개선

---

## Phase 3.1: Setup
- [ ] T001 Create Infrastructure data models directory structure
- [ ] T002 [P] Verify Python 3.13 environment and standard library dependencies
- [ ] T003 [P] Configure pytest for Infrastructure layer testing

## Phase 3.2: Contract Tests (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### OverlapAnalyzer v5.0 호환성 계약 테스트
- [ ] T004 [P] Contract test OverlapAnalyzer v5.0 interface compatibility in `tests/integration/overlap_analyzer_compatibility/test_overlap_interface.py`
- [ ] T005 [P] Contract test Repository interface compatibility in `tests/integration/overlap_analyzer_compatibility/test_repository_interface.py`
- [ ] T006 [P] Contract test data conversion compatibility in `tests/integration/overlap_analyzer_compatibility/test_data_conversion.py`

### 업비트 API 스키마 계약 테스트
- [ ] T007 [P] Contract test minute candle API schema in `tests/infrastructure/data_models/candle/test_upbit_minute_schema.py`
- [ ] T008 [P] Contract test daily candle API schema in `tests/infrastructure/data_models/candle/test_upbit_daily_schema.py`
- [ ] T009 [P] Contract test weekly/monthly candle API schema in `tests/infrastructure/data_models/candle/test_upbit_period_schema.py`

## Phase 3.3: Core Models Implementation (ONLY after tests are failing)

### 핵심 데이터 모델 구현
- [ ] T010 [P] Implement UpbitCandleModel in `upbit_auto_trading/infrastructure/data_models/candle/upbit_candle_model.py`
- [ ] T011 [P] Implement CandleDataTypes enums in `upbit_auto_trading/infrastructure/data_models/candle/candle_data_types.py`
- [ ] T012 [P] Implement ValidationRules module in `upbit_auto_trading/infrastructure/data_models/candle/validation_rules.py`

### 지원 모델 구현
- [ ] T013 [P] Implement TimeChunk model in `upbit_auto_trading/infrastructure/data_models/candle/time_chunk.py`
- [ ] T014 [P] Implement CandleDataResponse model in `upbit_auto_trading/infrastructure/data_models/candle/response_models.py`
- [ ] T015 [P] Implement OverlapStatus and DataRange models in `upbit_auto_trading/infrastructure/data_models/candle/overlap_models.py`

## Phase 3.4: Integration & Logging
- [ ] T016 Integrate Infrastructure logging with create_component_logger in all models
- [ ] T017 Update SqliteCandleRepository to support new model conversion (minimal changes)
- [ ] T018 Implement 200-chunk optimization in TimeChunk calculations
- [ ] T019 Add comprehensive error handling and logging for conversion failures

## Phase 3.5: Polish & Validation
- [ ] T020 [P] Unit tests for UpbitCandleModel validation rules in `tests/infrastructure/data_models/candle/test_validation_rules.py`
- [ ] T021 [P] Performance tests (baseline: 1000 models < 1s) in `tests/performance/test_model_performance.py`
- [ ] T022 [P] Memory usage tests for frozen dataclass efficiency in `tests/performance/test_memory_usage.py`
- [ ] T023 Execute quickstart.md validation scenarios end-to-end
- [ ] T024 Update module __init__.py files with proper exports
- [ ] T025 Final OverlapAnalyzer v5.0 regression test suite

---

## Dependencies

### Critical Path
1. **Setup** (T001-T003) → **Contract Tests** (T004-T009) → **Core Models** (T010-T015) → **Integration** (T016-T019) → **Polish** (T020-T025)

### Specific Dependencies
- T004-T009 must FAIL before any T010+ implementation
- T010 (UpbitCandleModel) blocks T013-T015 (dependent models)
- T016 (logging) blocks T017-T019 (repository integration)
- T017 (repository update) blocks T023 (quickstart validation)
- T020-T022 (tests) can run parallel with T024-T025 (docs)

### Parallel Execution Blockers
- T010-T012: Different files, can run in parallel
- T013-T015: Different files, can run in parallel
- T016-T019: Sequential (shared SqliteCandleRepository file)
- T020-T022: Different files, can run in parallel

---

## Parallel Execution Examples

### Phase 3.2: Contract Tests (All Parallel)
```bash
# Launch T004-T009 together:
Task: "Contract test OverlapAnalyzer v5.0 interface compatibility"
Task: "Contract test Repository interface compatibility"
Task: "Contract test data conversion compatibility"
Task: "Contract test minute candle API schema"
Task: "Contract test daily candle API schema"
Task: "Contract test weekly/monthly candle API schema"
```

### Phase 3.3: Core Models (Parallel Groups)
```bash
# Group 1: Core Models (T010-T012)
Task: "Implement UpbitCandleModel"
Task: "Implement CandleDataTypes enums"
Task: "Implement ValidationRules module"

# Group 2: Support Models (T013-T015)
Task: "Implement TimeChunk model"
Task: "Implement CandleDataResponse model"
Task: "Implement OverlapStatus and DataRange models"
```

### Phase 3.5: Polish Tests (Parallel)
```bash
# Launch T020-T022 together:
Task: "Unit tests for UpbitCandleModel validation rules"
Task: "Performance tests (baseline: 1000 models < 1s)"
Task: "Memory usage tests for frozen dataclass efficiency"
```

---

## Task Details

### Setup Tasks
**T001**: 디렉토리 구조 생성
- `upbit_auto_trading/infrastructure/data_models/candle/`
- `tests/infrastructure/data_models/candle/`
- `tests/integration/overlap_analyzer_compatibility/`
- `tests/performance/`

**T002**: 환경 검증
- Python 3.13 확인
- 표준 라이브러리 import 테스트 (dataclasses, datetime, enum, typing)
- SQLite3 접근 가능성 확인

**T003**: pytest 설정
- Infrastructure 레이어 테스트 설정
- TDD Red-Green-Refactor 사이클 준비

### Contract Test Tasks (Must Fail First)
**T004-T006**: OverlapAnalyzer v5.0 호환성
- 기존 인터페이스 시그니처 검증
- 데이터 변환 호환성 검증
- Repository 메서드 호환성 검증

**T007-T009**: 업비트 API 스키마 호환성
- 실제 API 응답 형식과의 정확한 매핑
- 타임프레임별 선택적 필드 처리
- 타입 안전성 검증

### Core Implementation Tasks
**T010**: UpbitCandleModel 구현
- frozen dataclass with all fields
- from_upbit_response() factory method
- to_repository_format() conversion
- to_db_format() conversion
- Data validation in __post_init__

**T011**: CandleDataTypes 구현
- OverlapStatus enum (5 states)
- TimeFrame enum
- DataSource enum
- Other supporting types

**T012**: ValidationRules 구현
- OHLC relationship validation
- Price positivity validation
- Volume/amount non-negativity validation
- TimeFrame-specific validation

**T013-T015**: 지원 모델 구현
- TimeChunk: 200개 청크 분할 최적화
- CandleDataResponse: 표준화된 응답 모델
- OverlapStatus/DataRange: OverlapAnalyzer 연동

### Integration Tasks
**T016**: Infrastructure 로깅 통합
- create_component_logger("CandleDataModel") 적용
- 에러 상황별 로깅 레벨 설정
- 성능 로깅 (변환 시간 등)

**T017**: Repository 연동
- SqliteCandleRepository 최소 변경
- 기존 메서드 시그니처 유지
- 새 모델 타입 지원 추가

**T018**: 청크 최적화
- 200개 단위 효율적 분할
- 메모리 사용량 최적화
- 처리 시간 단축

**T019**: 에러 처리
- 변환 실패 시 상세 에러 메시지
- 복구 가능한 에러와 치명적 에러 구분
- 로깅과 예외 처리 통합

### Polish Tasks
**T020-T022**: 성능 및 품질 검증
- 단위 테스트: 모든 validation 규칙
- 성능 테스트: 기준선 대비 성능 유지
- 메모리 테스트: frozen dataclass 효율성

**T023**: End-to-End 검증
- quickstart.md 시나리오 실행
- 실제 OverlapAnalyzer v5.0과 통합 테스트
- 회귀 테스트 실행

**T024-T025**: 마무리
- 모듈 exports 정리
- 최종 호환성 검증

---

## Validation Checklist
*GATE: All must pass before marking complete*

- [x] All contract files have corresponding test tasks
- [x] All entities in data-model.md have implementation tasks
- [x] All tests come before implementation (TDD enforced)
- [x] Parallel tasks use different files (no conflicts)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] OverlapAnalyzer v5.0 compatibility preserved
- [x] Performance baselines defined
- [x] Infrastructure logging integrated

**Ready for Implementation**: ✅ All validation gates passed
````
