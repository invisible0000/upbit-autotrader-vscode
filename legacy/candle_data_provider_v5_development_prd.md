# 📋 CandleDataProvider v5.0 - Product Requirements Document (PRD)
> GitHub Spec Kit 기반 완전 재개발 스펙

## 🎯 Problem & Users

### Problem Statement
**현재 상황**: 기반 인프라 컴포넌트들(TimeUtils, OverlapAnalyzer v5.0, CandleModels, SqliteCandleRepository)이 완성되었지만, 이들을 통합하는 CandleDataProvider가 기존 버전에서 완전히 업데이트되지 않아 메인 프로그램과 통합이 불가능한 상태

**핵심 문제**:
1. **아키텍처 불일치**: 기존 v4.0이 새로운 OverlapAnalyzer v5.0 5-state 분류와 호환되지 않음
2. **모델 불일치**: 새로운 CandleData 모델과 CandleDataResponse 구조와 맞지 않음
3. **Repository 인터페이스 변경**: 새로운 CandleRepositoryInterface 10개 메서드와 연동 필요
4. **시간 처리 개선**: TimeUtils의 새로운 timedelta 기반 처리 방식 적용 필요
5. **통합 검증 부족**: 메인 프로그램 통합을 위한 검증 체계 부재

### Target Users
- **Application Layer 서비스들**: 캔들 데이터를 필요로 하는 비즈니스 로직
- **자동매매 전략 엔진**: 실시간/히스토리 캔들 데이터 소비자
- **차트 시각화 모듈**: UI Layer에서 차트 표시용 데이터 요청
- **백테스팅 시스템**: 대량의 히스토리 데이터 처리 필요
- **개발자**: 메인 프로그램에서 `python run_desktop_ui.py` 실행시 안정적 동작 보장

### Value Proposition
- **단일 진입점**: 모든 캔들 데이터 요청을 하나의 인터페이스로 처리
- **최적화된 성능**: OverlapAnalyzer v5.0의 309배 성능 향상 활용
- **완전한 통합**: 5개 기반 컴포넌트의 완벽한 조화
- **메인 프로그램 호환**: 즉시 프로덕션 환경에서 사용 가능

---

## 🎯 Goals & Non-goals

### Primary Goals
1. **완전한 기반 컴포넌트 통합**
   - OverlapAnalyzer v5.0의 5-state 분류 (NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS) 완전 활용
   - TimeUtils의 timedelta 기반 시간 처리 및 27개 타임프레임 지원
   - 새로운 CandleData 모델의 업비트 API 호환성 활용
   - SqliteCandleRepository의 10개 최적화된 메서드 활용

2. **DDD Infrastructure Layer 완전 준수**
   - Domain Layer 의존성 없음 (순수 Infrastructure Service)
   - Repository 패턴을 통한 데이터 접근 추상화
   - Infrastructure 로깅 (`create_component_logger`) 일관성 유지

3. **5가지 파라미터 조합 지원**
   - `count만`: 최신 데이터부터 역순
   - `start_time + count`: 특정 시점부터 개수 지정
   - `start_time + end_time`: 구간 지정 (inclusive_start 처리)
   - 미래 시간 요청 검증 및 ValidationError 처리
   - 대량 요청시 200개 청크 자동 분할

4. **메인 프로그램 통합 검증**
   - `python run_desktop_ui.py` 실행시 오류 없음
   - 기존 7규칙 전략과 완전 호환
   - UI Layer에서 차트 데이터 요청 처리

### Secondary Goals
- **캐시 최적화**: 60초 TTL 메모리 캐시로 반복 요청 성능 향상
- **통계 수집**: API 요청 수, 응답 시간, 캐시 히트율 등 모니터링
- **에러 복구**: Rate limit, 네트워크 오류시 지수 백오프 재시도

### Non-goals
- **새로운 기능 추가**: 기존 요구사항 외 추가 기능 개발 안함
- **UI 로직 포함**: Presentation Layer 관련 로직 포함 안함
- **비즈니스 로직**: Domain Layer 책임인 거래 로직 포함 안함
- **다른 거래소 지원**: 업비트 외 거래소 지원 안함

---

## 🏗️ Scope & UX Flows

### Technical Scope

#### Core Components Integration
```
CandleDataProvider v5.0
├── OverlapAnalyzer v5.0 (5-state classification)
├── TimeUtils (timedelta-based, 27 timeframes)
├── CandleModels (CandleData + CandleDataResponse)
├── SqliteCandleRepository (10 optimized methods)
└── CandleRepositoryInterface (DDD compliance)
```

#### Public API Surface
```python
class CandleDataProvider:
    # === Main Entry Point ===
    async def get_candles(
        symbol: str,
        timeframe: str,
        count: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        inclusive_start: bool = True
    ) -> CandleDataResponse

    # === Convenience Methods ===
    async def get_latest_candles(symbol: str, timeframe: str, count: int = 200) -> CandleDataResponse

    # === Statistics & Health ===
    def get_stats() -> dict
    def get_supported_timeframes() -> List[str]
    def get_cache_stats() -> dict
```

### UX Flow Scenarios

#### Scenario 1: Application Layer - 최신 데이터 요청
```python
# 사용자: Application Layer Service
provider = CandleDataProvider(db_manager, upbit_client)
response = await provider.get_candles("KRW-BTC", "5m", count=100)

# 내부 흐름:
# 1. 파라미터 검증 및 표준화
# 2. 캐시 확인 (60초 TTL)
# 3. OverlapAnalyzer로 겹침 분석
# 4. DB/API 혼합 수집 (최적화)
# 5. CandleDataResponse 반환
```

#### Scenario 2: 백테스팅 - 대량 히스토리 데이터
```python
# 사용자: 백테스팅 시스템
start_time = datetime(2024, 1, 1)
end_time = datetime(2024, 12, 31)
response = await provider.get_candles("KRW-BTC", "1d", start_time=start_time, end_time=end_time)

# 내부 흐름:
# 1. 시간 범위 → 예상 개수 계산 (TimeUtils)
# 2. 200개 청크로 자동 분할
# 3. 각 청크별 OverlapAnalyzer 분석
# 4. 순차 수집 (target_end_time 도달시 중단)
# 5. 중복 제거 및 시간순 정렬
```

#### Scenario 3: UI Layer - 실시간 차트 업데이트
```python
# 사용자: PyQt6 차트 위젯
response = await provider.get_latest_candles("KRW-BTC", "1m", count=100)

# 내부 흐름:
# 1. 캐시 우선 확인 (실시간 요청은 캐시 효과 높음)
# 2. 캐시 미스시 DB 우선 조회
# 3. 최신 데이터 부족시만 API 요청
# 4. 빠른 응답 (평균 50ms 이하)
```

---

## 🔒 Constraints

### Technical Constraints
1. **업비트 API 제한**
   - 분당 600회 요청 제한 (Rate Limiting)
   - 1회당 최대 200개 캔들 수집
   - API 키 보안 (ApiKeyService 활용)

2. **DDD Architecture 준수**
   - Domain Layer 의존성 금지
   - Infrastructure Layer만 사용
   - Repository 패턴 강제 적용

3. **성능 요구사항**
   - 100개 캔들: 평균 50ms 이하
   - 1000개 캔들: 평균 500ms 이하
   - 캐시 히트율: 80% 이상 (실시간 요청)

4. **메모리 제약**
   - 캐시 최대 100MB
   - 청크 처리로 메모리 사용량 제한
   - 대량 요청시 스트리밍 처리

### Business Constraints
1. **업비트 데이터 무결성**
   - 공식 API 데이터만 사용
   - 캔들 시간 정확성 보장
   - 가격 데이터 정밀도 유지

2. **Dry-Run 우선 원칙**
   - 테스트 환경에서 충분한 검증 후 적용
   - 메인 프로그램 통합시 안정성 최우선

### Operational Constraints
1. **Windows PowerShell 환경**
   - Unix 명령어 사용 금지
   - PowerShell 스크립트 호환성

2. **3-DB 분리 원칙**
   - market_data.sqlite3 전용 사용
   - 다른 DB와 격리 유지

---

## 🔗 Dependencies

### Direct Dependencies (기반 컴포넌트)
1. **OverlapAnalyzer v5.0** (`overlap_analyzer.py`)
   - 5-state classification (NO_OVERLAP → PARTIAL_MIDDLE_CONTINUOUS)
   - analyze_overlap() 메서드로 API 요청 최적화
   - OverlapRequest/OverlapResult 모델 사용

2. **TimeUtils** (`time_utils.py`)
   - 27개 타임프레임 지원 (1s~1y)
   - timedelta 기반 고속 계산
   - get_timeframe_seconds(), calculate_expected_count() 활용

3. **CandleModels** (`candle_models.py`)
   - CandleData: 업비트 API 완전 호환 모델
   - CandleDataResponse: 서비스 응답 표준화
   - CandleChunk: 200개 청크 처리 단위

4. **SqliteCandleRepository** (`sqlite_candle_repository.py`)
   - 10개 최적화된 메서드 (LEAD 윈도우 함수 등)
   - has_any_data_in_range(), is_range_complete() 등
   - DDD CandleRepositoryInterface 구현

5. **CandleRepositoryInterface** (`candle_repository_interface.py`)
   - Domain Layer 추상화
   - 10개 abstract method 정의
   - DataRange 모델 지원

### Infrastructure Dependencies
- **DatabaseManager**: Connection pooling + WAL 모드
- **UpbitPublicClient**: REST API 클라이언트
- **Infrastructure Logging**: create_component_logger 일관성

### External Dependencies
- **Upbit API**: 공식 REST API
- **SQLite3**: 로컬 캔들 데이터 저장
- **asyncio**: 비동기 처리 (API 요청, DB 액세스)

---

## ✅ Acceptance Criteria

### Functional Requirements

#### AC-1: 기반 컴포넌트 완전 통합
- [ ] OverlapAnalyzer v5.0의 5가지 상태 모두 처리
- [ ] TimeUtils의 27개 타임프레임 모두 지원
- [ ] CandleData 모델 100% 호환
- [ ] SqliteCandleRepository 10개 메서드 모두 활용
- [ ] CandleRepositoryInterface 완전 준수

#### AC-2: 5가지 파라미터 조합 지원
- [ ] `count만`: 최신 200개 캔들 정상 수집
- [ ] `start_time + count`: 특정 시점부터 정확한 개수 수집
- [ ] `start_time + end_time`: 구간 지정 정확한 범위 수집
- [ ] `inclusive_start=True`: start_time 포함하여 수집
- [ ] `inclusive_start=False`: 업비트 API 네이티브 동작

#### AC-3: 성능 최적화
- [ ] 100개 캔들: 평균 50ms 이하 응답
- [ ] 1000개 캔들: 평균 500ms 이하 응답
- [ ] 캐시 히트율: 80% 이상 (동일 요청 반복시)
- [ ] API 요청 최적화: 기존 데이터 중복 요청 0%

#### AC-4: 청크 처리
- [ ] 200개 초과 요청시 자동 청크 분할
- [ ] 각 청크별 OverlapAnalyzer 최적화 적용
- [ ] target_end_time 도달시 자동 중단
- [ ] 메모리 사용량 100MB 이하 유지

### Non-Functional Requirements

#### AC-5: DDD Architecture 준수
- [ ] Domain Layer import 없음
- [ ] Infrastructure Layer만 사용
- [ ] Repository 패턴 일관성
- [ ] create_component_logger 로깅 사용

#### AC-6: 에러 처리
- [ ] 미래 시간 요청시 ValidationError
- [ ] Rate limit 초과시 지수 백오프
- [ ] 네트워크 오류시 재시도 (최대 3회)
- [ ] DB 연결 실패시 graceful degradation

#### AC-7: 메인 프로그램 통합
- [ ] `python run_desktop_ui.py` 오류 없이 실행
- [ ] 기존 7규칙 전략과 호환
- [ ] UI 차트에서 데이터 정상 표시
- [ ] 자동매매 시스템에서 실시간 데이터 활용

### Quality Gates

#### AC-8: 테스트 커버리지
- [ ] 단위 테스트: 모든 public 메서드
- [ ] 통합 테스트: 기반 컴포넌트와의 연동
- [ ] 성능 테스트: 응답 시간 검증
- [ ] 메인 프로그램 검증: UI 실행 테스트

#### AC-9: 코드 품질
- [ ] Pylance 정적 분석 통과
- [ ] 타입 힌트 100% 적용
- [ ] 로깅 일관성 유지
- [ ] 예외 처리 완전성

---

## 🔍 Observability

### Logging Strategy
```python
logger = create_component_logger("CandleDataProvider")

# 요청 추적
logger.info(f"캔들 데이터 요청: {symbol} {timeframe} count={count}")

# 성능 모니터링
logger.debug(f"OverlapAnalyzer 분석 완료: {overlap_result.status} ({elapsed_ms:.2f}ms)")

# 캐시 효율성
logger.debug(f"캐시 히트! 즉시 반환: {len(cache_result)}개 캔들 ({response_time:.2f}ms)")

# 청크 처리
logger.debug(f"청크 {chunk_index+1}/{total_chunks} 수집 완료: {len(candles)}개 ({data_source})")
```

### Metrics Collection
- **응답 시간**: 평균/최대/95퍼센타일
- **캐시 효율**: 히트율/미스율/만료율
- **API 사용량**: 요청 수/Rate limit 상태
- **청크 통계**: 평균 청크 수/처리 시간

### Recovery Plan
1. **API Rate Limit**: 지수 백오프 후 재시도
2. **DB 연결 실패**: 캐시만으로 동작, 경고 로그
3. **메모리 부족**: 캐시 자동 정리, 청크 크기 축소
4. **데이터 불일치**: 강제 새로고침, 에러 로그

---

## ⚠️ Risks & Rollback

### High-Risk Areas
1. **OverlapAnalyzer 통합 실패**
   - **위험**: 5-state 분류 처리 오류로 성능 저하
   - **완화**: 기존 v4.0 로직 백업, 단계적 통합
   - **롤백**: overlap_analyzer.py 비활성화 모드

2. **메인 프로그램 통합 오류**
   - **위험**: UI 실행시 캔들 데이터 로딩 실패
   - **완화**: 철저한 통합 테스트, 단계적 배포
   - **롤백**: 기존 CandleDataProvider v4.0 복원

3. **성능 회귀**
   - **위험**: 새로운 구조로 인한 응답 시간 증가
   - **완화**: 성능 벤치마크 테스트 필수
   - **롤백**: 성능 기준 미달시 최적화 재작업

### Medium-Risk Areas
1. **메모리 누수**: 캐시 정리 로직 오류
2. **Rate Limit 초과**: API 요청 최적화 실패
3. **데이터 무결성**: 시간 처리 오류로 인한 중복/누락

### Rollback Strategy
1. **즉시 롤백** (Critical Issues)
   ```powershell
   # 기존 파일 복원
   Copy-Item "candle_data_provider_v4_backup.py" "candle_data_provider.py"
   python run_desktop_ui.py  # 검증
   ```

2. **선택적 롤백** (Partial Issues)
   - 문제 컴포넌트만 비활성화
   - 기존 로직으로 폴백 처리
   - 점진적 수정 적용

3. **데이터 롤백** (DB Issues)
   - SQLite WAL 파일 롤백
   - 캐시 완전 초기화
   - 강제 API 요청 모드

---

## 📅 Implementation Timeline

### Phase 1: Core Integration (1-2 hours)
- [ ] 기본 클래스 구조 재작성
- [ ] 5개 기반 컴포넌트 import 및 초기화
- [ ] get_candles() 메서드 시그니처 정의

### Phase 2: Core Logic Implementation (2-3 hours)
- [ ] 파라미터 검증 및 표준화 로직
- [ ] OverlapAnalyzer v5.0 통합
- [ ] 청크 분할 및 순차 수집 로직
- [ ] 응답 조합 및 최적화

### Phase 3: Testing & Validation (1-2 hours)
- [ ] 단위 테스트 작성 및 실행
- [ ] 성능 벤치마크 테스트
- [ ] 메인 프로그램 통합 검증

### Phase 4: Final Polish (30min)
- [ ] 로깅 최적화
- [ ] 에러 처리 강화
- [ ] 문서 업데이트

### Total Estimated Time: 4-7 hours

---

## 📝 Success Metrics

### MVP Success Criteria
1. **기능적 성공**: 모든 AC 1-7 달성
2. **성능 성공**: 응답 시간 기준 충족
3. **통합 성공**: `python run_desktop_ui.py` 정상 실행
4. **품질 성공**: 모든 테스트 통과

### Long-term Success Indicators
- **안정성**: 7일간 오류 없는 운영
- **효율성**: API 요청 50% 이상 감소
- **유지보수성**: 새로운 기능 추가시 수정 최소화
- **개발자 만족도**: 사용하기 쉬운 인터페이스

---

**승인 대기**: 이 PRD가 승인되면 Phase 1부터 순차적으로 구현을 시작합니다.
