# Research Report: OverlapAnalyzer v5.0 Infrastructure 레이어 모델 재개발

**연구 범위**: OverlapAnalyzer v5.0 호환성, 업비트 API 스키마, Infrastructure 모델 설계
**완료일**: 2025-09-10

## 핵심 연구 결과

### 1. OverlapAnalyzer v5.0 현재 인터페이스 분석

**Decision**: OverlapAnalyzer v5.0는 5가지 겹침 상태 분류 엔진으로 완전 구현됨
**Rationale**:
- `OverlapRequest` (symbol, timeframe, target_start, target_end, target_count)
- `OverlapResult` (status, api_start, partial_start)
- 5가지 상태: NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS
- CandleRepositoryInterface 의존: Repository 패턴으로 완전 분리된 설계

**Alternatives considered**:
- 직접 DB 접근 → 기각 (DDD 위반)
- 새로운 인터페이스 설계 → 기각 (호환성 보장 원칙)

### 2. SqliteCandleRepository 현재 구조 분석

**Decision**: 기존 Repository 최소 변경으로 Infrastructure 모델 통합
**Rationale**:
- 현재 12개 주요 메서드 (`has_any_data_in_range`, `is_range_complete`, `find_last_continuous_time` 등)
- `_to_utc_iso`, `_from_utc_iso` 유틸리티로 datetime↔string 변환 완료
- OverlapAnalyzer 전용 메서드들: `get_data_ranges`, `count_candles_in_range`, `has_data_at_time`
- save/get 기본 메서드: `save_candle_chunk`, `get_candles_by_range`

**Alternatives considered**:
- Repository 전면 재작성 → 기각 (변경 최소화 원칙)
- 새로운 Repository 생성 → 기각 (중복 방지)

### 3. 업비트 API 캔들 데이터 스키마 완전 분석

**Decision**: 업비트 REST API 완전 호환 스키마 모델 설계
**Rationale**:
- **공통 필드 (9개)**: market, candle_date_time_utc, candle_date_time_kst, opening_price, high_price, low_price, trade_price, timestamp, candle_acc_trade_price, candle_acc_trade_volume
- **타임프레임별 선택적 필드**:
  - unit (분봉): 1, 3, 5, 10, 15, 30, 60, 240분 단위
  - prev_closing_price (일봉만): 전일 종가
  - first_day_of_period (주/월/연봉): 집계 시작일
- **데이터 타입**: string, double, int64, integer → Python: str, float, int
- **시간 형식**: UTC/KST 모두 ISO 8601 ('2025-06-30T00:00:00')
- **DB 저장**: 공통 필드 9개 + created_at + 타임프레임별 선택적 필드
- **계산 필드**: change_price, change_rate는 DB 저장하지 않고 프로퍼티로 제공 (일봉만 해당)

**Alternatives considered**:
- 단순화된 모델 → 기각 (완전 호환성 필요)
- 별도 타임프레임 모델 → 기각 (복잡성 증가)
- 환산 통화 저장 → 기각 (API 요청 시마다 계산되므로 불필요)

### 4. 200개 청크 분할 최적화 전략

**Decision**: TimeChunk 모델로 청크 분할 메타데이터 관리
**Rationale**:
- 업비트 API 제한: 최대 200개 캔들/요청
- 청크 정보: start_time, end_time, expected_count, chunk_index
- 순차 처리: API Rate Limit 준수
- 메모리 효율성: 청크별 처리로 대용량 데이터 최적화

**Alternatives considered**:
- 동시 청크 처리 → 기각 (Rate Limit 위험)
- 가변 청크 크기 → 기각 (복잡성 불필요)

### 5. Infrastructure 로깅 시스템 통합

**Decision**: create_component_logger("CandleDataModel") 패턴 사용
**Rationale**:
- 기존 OverlapAnalyzer 로깅: `logger = create_component_logger("OverlapAnalyzer")`
- Infrastructure 계층 표준: 컴포넌트별 로거 분리
- 구조화된 로깅: JSON 형식, 컨텍스트 정보 포함
- 통합 로그 스트림: 모든 Infrastructure 컴포넌트 동일 형식

**Alternatives considered**:
- 표준 logging → 기각 (Infrastructure 표준 위반)
- 별도 로깅 시스템 → 기각 (통합성 저해)

## 기술 스택 결정

### 핵심 라이브러리
- **dataclasses**: 모델 정의 (Python 3.7+ 표준)
- **datetime**: 시간 처리 (표준 라이브러리)
- **enum**: 상태 관리 (표준 라이브러리)
- **typing**: 타입 힌트 (표준 라이브러리)

### 의존성 분석
- **외부 의존성**: 없음 (표준 라이브러리만 사용)
- **내부 의존성**:
  - upbit_auto_trading.infrastructure.logging (로깅)
  - 기존 OverlapAnalyzer 인터페이스 호환성

### 성능 벤치마크 목표
- **메모리 사용량**: 기존 대비 20% 절약
- **객체 생성 속도**: 기존과 동일 또는 향상
- **시간 계산 정확성**: 100% (기존 테스트 통과)

## 아키텍처 결정

### 모듈 구조
```
upbit_auto_trading/infrastructure/market_data/candle/
├── models.py          # 새로 재개발
├── time_utils.py      # 새로 재개발
├── overlap_analyzer.py # 기존 유지 (검증됨)
└── __init__.py
```

### 클래스 계층 구조
- **CandleData**: 핵심 데이터 모델
- **TimeUtils**: 정적 메서드 유틸리티 클래스
- **응답 모델들**: CandleDataResponse, OverlapResult 등
- **캐시 모델들**: CacheKey, CacheEntry 등

### 인터페이스 호환성
- 기존 OverlapAnalyzer가 사용하는 모든 메서드 시그니처 유지
- 새로운 기능은 추가 메서드로 제공 (기존 코드 영향 없음)

## 검증 계획

### 1. 호환성 검증
- 기존 OverlapAnalyzer v5.0 테스트 스위트 통과
- 실제 업비트 API 데이터로 검증

### 2. 성능 검증
- 200개 캔들 처리 성능 측정
- 메모리 사용량 프로파일링

### 3. 정확성 검증
- 시간 계산 결과 기존 구현과 비교
- 업비트 API 응답 파싱 정확성 검증

## 위험 요소 및 완화 방안

### 위험 요소
1. **호환성 깨짐**: 기존 OverlapAnalyzer 동작 변경
2. **성능 저하**: 새로운 구조로 인한 성능 이슈
3. **복잡성 증가**: 과도한 추상화

### 완화 방안
1. **점진적 전환**: 기존 코드 유지하며 새 모델 병행 테스트
2. **성능 모니터링**: 각 단계별 성능 측정 및 비교
3. **단순성 유지**: Constitution Check 엄격 적용

## 구현 우선순위

### Phase 1: 핵심 모델
1. CandleData 클래스 (업비트 API 완전 호환)
2. 기본 검증 로직
3. OverlapAnalyzer 호환성 테스트

### Phase 2: 시간 유틸리티
1. TimeUtils 클래스 (기존 로직 이식)
2. 5가지 파라미터 조합 처리
3. 청크 분할 기능

### Phase 3: 확장 모델
1. 응답/요청 모델들
2. 캐시 관련 모델들
3. 통계 모델들

### Phase 4: 통합 및 최적화
1. 전체 시스템 통합
2. 성능 최적화
3. 문서화 완료
