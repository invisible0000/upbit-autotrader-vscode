# 📋 ChunkProcessor v2.0 마이그레이션 PRD (Product Requirements Document)

> **프로젝트**: 업비트 자동매매 시스템
> **작성일**: 2025년 9월 23일
> **버전**: v2.0
> **승인 상태**: Draft → Review Pending

---

## 🎯 Problem & Users

### 현재 문제점
1. **복잡한 4단계 파이프라인**: v7.0 ChunkProcessor의 불필요한 추상화로 인한 성능 저하
2. **독립적 사용 불가**: CandleDataProvider의 CollectionState에 의존하여 코인 스크리너 등에서 단독 사용 불가
3. **Legacy 로직 누락**: 검증된 candle_data_provider_original.py의 핵심 로직 일부 미반영
4. **UI 연동 부재**: 실시간 진행 상황 모니터링 기능 없음

### 대상 사용자
- **Primary**: 업비트 자동매매 시스템 내부 컴포넌트 (CandleDataProvider)
- **Secondary**: 독립적 캔들 수집이 필요한 도구 (코인 스크리너, 백테스트 엔진)
- **Tertiary**: UI 개발자 (진행 상황 모니터링 필요)

### 비즈니스 가치
- **성능 개선**: 메모리 90% 절약, DB 접근 56% 감소 (Legacy 수준 달성)
- **재사용성 증대**: ChunkProcessor 독립 사용으로 새로운 도구 개발 가속화
- **사용자 경험**: Progress Callback을 통한 실시간 피드백 제공

---

## 🎯 Goals & Non-goals

### Goals (달성 목표)
1. **Legacy 로직 100% 보존**: candle_data_provider_original.py의 검증된 로직 완전 이식
2. **독립적 사용 지원**: ChunkProcessor만으로 완전한 캔들 수집 가능
3. **UI 연동 지원**: Progress Callback을 통한 실시간 진행 상황 보고
4. **기존 호환성 유지**: 현재 CandleDataProvider 인터페이스 100% 호환
5. **성능 최적화**: Legacy 수준의 메모리/CPU/DB 효율성 달성

### Non-goals (비목표)
- ❌ 새로운 캔들 데이터 소스 추가 (업비트 API 외)
- ❌ 캔들 데이터 포맷 변경
- ❌ 기존 빈 캔들 처리 로직 수정
- ❌ OverlapAnalyzer 알고리즘 변경
- ❌ EmptyCandleDetector 로직 변경

---

## 🔍 Scope & UX flows

### 개발 범위

#### In-Scope
1. **ChunkProcessor v2.0 클래스 신규 개발**
   - Legacy 메서드 6개 완전 이식
   - 이중 인터페이스 구현 (독립 사용 + CandleDataProvider 연동)
   - Progress Reporting 시스템 구현

2. **CandleDataProvider 간소화**
   - 1,200줄 → 300줄 (75% 감소)
   - ChunkProcessor 위임 구조로 변경
   - 기존 호환성 메서드 유지

3. **데이터 모델 확장**
   - CollectionProgress, CollectionResult 추가
   - 기존 ChunkResult, ChunkInfo 유지

#### Out-of-Scope
- 기존 Repository, UpbitClient, OverlapAnalyzer 변경
- 데이터베이스 스키마 변경
- UI 컴포넌트 개발 (Progress Callback 소비자는 별도 구현)

### UX Flow (개발자 경험)

#### Flow 1: 독립적 사용 (코인 스크리너)
```python
# Before: 불가능 (CandleDataProvider 의존)

# After: 완전 독립적 사용
chunk_processor = ChunkProcessor(...)
result = await chunk_processor.execute_full_collection(
    symbol='KRW-BTC', timeframe='1m', count=1000,
    progress_callback=update_ui
)
```

#### Flow 2: 기존 호환성 (CandleDataProvider)
```python
# Before: 복잡한 내부 로직
provider = CandleDataProvider(...)
candles = await provider.get_candles('KRW-BTC', '1m', 1000)

# After: 동일한 인터페이스, 내부는 ChunkProcessor 위임
provider = CandleDataProvider(...)  # 내부적으로 ChunkProcessor 사용
candles = await provider.get_candles('KRW-BTC', '1m', 1000)  # 동일한 API
```

#### Flow 3: 실시간 모니터링
```python
# Before: 진행 상황 알 수 없음

# After: 실시간 Progress 업데이트
def show_progress(progress: CollectionProgress):
    print(f"{progress.symbol}: {progress.current_chunk}/{progress.total_chunks}")

result = await chunk_processor.execute_full_collection(
    ..., progress_callback=show_progress
)
```

---

## 🔒 Constraints

### API Rate-limit
- **업비트 제한**: 10 RPS (초당 10회 요청)
- **청크 크기**: 최대 200개 캔들 (업비트 제한)
- **대응**: 기존 백오프 로직 유지

### Security
- **API 키 보호**: ApiKeyService 암호화 저장 유지 (메모리 TTL 5분)
- **로그 보안**: API 키 등 민감 정보 로그/테스트에 노출 금지
- **DDD 준수**: Domain 계층 외부 의존성 금지 유지

### Performance
- **메모리 효율성**: Legacy 수준 (90% 절약) 달성 필수
- **DB 접근 최소화**: Legacy 수준 (56% 감소) 달성 필수
- **CPU 처리량**: Legacy 수준 (70% 개선) 달성 필수

### Platform
- **Windows PowerShell 전용**: Unix 명령어 사용 금지
- **Python 환경**: 기존 의존성 패키지 버전 유지
- **VS Code 통합**: 기존 개발 환경과의 완전 호환

---

## 🔗 Dependencies

### Internal Dependencies
1. **CandleRepositoryInterface**: 기존 인터페이스 그대로 사용
2. **UpbitPublicClient**: API 호출 클라이언트 (기존 유지)
3. **OverlapAnalyzer**: 겹침 분석 로직 (기존 유지)
4. **EmptyCandleDetector**: 빈 캔들 처리 (기존 유지)
5. **TimeUtils**: 시간 계산 유틸리티 (기존 유지)

### External Dependencies
- **없음**: 기존 패키지 의존성 변경 없음

### Migration Dependencies
1. **candle_data_provider_original.py**: Legacy 로직 참조 소스
2. **기존 단위 테스트**: 호환성 검증 기준
3. **CHUNK_PROCESSOR_v2.md**: 상세 설계서

---

## ✅ Acceptance Criteria

### Phase 1: ChunkProcessor v2.0 구현 (1주)
- [ ] ChunkProcessor 클래스 기본 구조 생성 완료
- [ ] Legacy 메서드 6개 완전 이식 완료
  - [ ] `_process_chunk_direct_storage()` → `_process_current_chunk()`
  - [ ] `_handle_overlap_direct_storage()` → `_handle_overlap()`
  - [ ] `_fetch_chunk_from_api()` → `_fetch_from_api()`
  - [ ] `_analyze_chunk_overlap()` → `_analyze_overlap()`
  - [ ] `_process_api_candles_with_empty_filling()` → `_process_empty_candles()`
  - [ ] `plan_collection()` → `_plan_collection()`
- [ ] `execute_full_collection()` 메인 메서드 구현 완료
- [ ] Progress Reporting 시스템 구현 완료
- [ ] 독립 단위 테스트 작성 완료

### Phase 2: CandleDataProvider 간소화 (3일)
- [ ] `get_candles()` 메서드 ChunkProcessor 위임으로 간소화
- [ ] 기존 호환성 메서드들 ChunkProcessor 위임으로 변경
- [ ] 복잡한 상태 관리 로직 제거
- [ ] `execute_single_chunk()` 연동 구현 완료

### Phase 3: 통합 테스트 및 검증 (2일)
- [ ] 기존 단위 테스트 모두 통과 확인
- [ ] 성능 회귀 테스트 통과 (메모리, 실행시간 ±10% 이내)
- [ ] 실제 데이터로 수집 테스트 완료
- [ ] UI 통합 테스트 완료 (`python run_desktop_ui.py`)
- [ ] 독립 사용 시나리오 테스트 완료

### Phase 4: 문서화 및 배포 (1일)
- [ ] API 문서 업데이트 완료
- [ ] 사용 예시 가이드 작성 완료
- [ ] 기존 코드 Legacy 백업 완료
- [ ] 프로덕션 배포 완료

### 최종 검증 기준
- ✅ `python run_desktop_ui.py` 정상 실행
- ✅ 트리거 빌더에서 7규칙 전략 구성 가능
- ✅ Legacy 대비 성능 회귀 없음 (±10% 이내)
- ✅ 독립적 캔들 수집 정상 동작
- ✅ 실시간 Progress 보고 정상 동작

---

## 📊 Observability

### 로깅 전략
- **Component Logger**: `create_component_logger("ChunkProcessor")` 사용
- **Legacy 호환**: 기존 로깅 레벨 및 형식 유지
- **Progress 로깅**: DEBUG 레벨로 상세한 진행 상황 기록
- **성능 메트릭**: 메모리, DB 접근, API 호출 횟수 추적

### 메트릭 수집
```python
# Progress 콜백에서 메트릭 수집
def track_metrics(progress: CollectionProgress):
    metrics = {
        'chunks_processed': progress.current_chunk,
        'elapsed_seconds': progress.elapsed_seconds,
        'memory_usage_mb': get_memory_usage(),
        'api_calls_made': progress.api_calls_made
    }
```

### 에러 추적
- **청크별 실패 추적**: error_chunk_id로 특정 청크 실패 지점 파악
- **단계별 실패 분석**: Progress 상태별 실패 패턴 분석
- **Recovery 로직**: Legacy와 동일한 에러 복구 메커니즘 유지

---

## ⚠️ Risks & Rollback

### High Risk
1. **Legacy 로직 미스매치**
   - **위험**: 이식 과정에서 미묘한 로직 차이 발생
   - **완화**: Legacy 코드와 1:1 비교 테스트 필수
   - **롤백**: candle_data_provider_original.py 즉시 복원

2. **성능 회귀**
   - **위험**: 메모리/CPU 사용량 증가로 시스템 부하
   - **완화**: 각 Phase별 성능 벤치마크 테스트
   - **롤백**: 성능 기준 미달시 즉시 Legacy 복원

### Medium Risk
3. **기존 호환성 깨짐**
   - **위험**: CandleDataProvider 인터페이스 변경으로 기존 코드 오동작
   - **완화**: 기존 단위 테스트 100% 통과 필수
   - **롤백**: 인터페이스 차이 발생시 즉시 수정 또는 복원

4. **UI 연동 실패**
   - **위험**: Progress Callback 메커니즘의 메모리 누수 또는 성능 이슈
   - **완화**: Progress Callback 옵셔널 설계 + 독립 테스트
   - **롤백**: Progress 기능 비활성화 후 배포

### Low Risk
5. **문서화 지연**
   - **위험**: 개발 완료 후 문서화 지연으로 유지보수성 저하
   - **완화**: Phase별 동시 문서화 진행
   - **롤백**: 핵심 API 문서만 우선 작성

### Rollback Strategy
```bash
# 긴급 롤백 절차 (PowerShell)
# 1. Legacy 백업 복원
Copy-Item "backups\candle_data_provider_original.py" "candle_data_provider.py" -Force

# 2. 새 파일 제거
Remove-Item "chunk_processor_v2.py" -ErrorAction SilentlyContinue

# 3. 테스트 실행으로 검증
python -m pytest tests\infrastructure\market_data\candle\ -v

# 4. UI 통합 테스트
python run_desktop_ui.py
```

---

## 📈 Success Metrics

### 성능 메트릭
- **메모리 사용량**: Legacy 대비 90% 절약 (1GB → 100MB) 달성
- **DB 접근 횟수**: Legacy 대비 56% 감소 (16회 → 7회) 달성
- **CPU 처리 시간**: Legacy 대비 70% 개선 달성
- **API 호출 효율성**: OverlapAnalyzer로 인한 API 절약 효과 유지

### 기능 메트릭
- **Legacy 호환성**: 기존 단위 테스트 100% 통과
- **독립 사용성**: ChunkProcessor만으로 완전한 수집 성공률 100%
- **UI 연동**: Progress Callback 정상 동작률 100%
- **오류 복구**: 실패 청크에 대한 자동 복구 성공률 ≥95%

### 개발 생산성 메트릭
- **코드 복잡도**: CandleDataProvider 75% 감소 (1,200줄 → 300줄)
- **테스트 커버리지**: 핵심 로직 ≥95% 커버리지 유지
- **개발 속도**: 새로운 캔들 수집 도구 개발 시간 50% 단축

---

## 🎯 Milestones & Timeline

### Week 1: ChunkProcessor v2.0 구현
- **Day 1-2**: 기본 구조 및 데이터 모델 구현
- **Day 3-4**: Legacy 메서드 6개 이식
- **Day 5**: `execute_full_collection()` 메인 로직 구현
- **Day 6-7**: Progress Reporting 시스템 및 단위 테스트

### Week 1.5: CandleDataProvider 간소화
- **Day 1**: `get_candles()` 간소화 및 위임 구현
- **Day 2**: 기존 호환성 메서드들 위임으로 변경
- **Day 3**: `execute_single_chunk()` 연동 및 테스트

### Week 2: 통합 테스트 및 검증
- **Day 1**: Legacy 호환성 테스트 및 성능 벤치마크
- **Day 2**: 실제 데이터 수집 테스트 및 UI 통합 테스트

### Week 2.5: 문서화 및 배포
- **Day 1**: API 문서 작성 및 Legacy 백업 완료

---

## 💡 Implementation Notes

### 핵심 설계 원칙
1. **Legacy First**: 새로운 기능보다 기존 로직 보존 우선
2. **Minimal Change**: 구조 변경만 하고 로직은 그대로
3. **Single Responsibility**: ChunkProcessor는 청크 처리만, CandleDataProvider는 인터페이스만
4. **Clean Interface**: 사용하기 쉬운 깔끔한 API 제공

### 중요 구현 고려사항
- **UTC 시간 통일**: 기존 TimeUtils.normalize_datetime_to_utc() 활용
- **DDD 아키텍처 준수**: Domain 계층 외부 의존성 금지
- **Infrastructure 로깅**: create_component_logger 사용 필수
- **Dry-Run 기본값**: 모든 주문은 기본 dry_run=True

### 테스트 전략
- **Legacy 호환성**: 동일 조건 동일 결과 보장 테스트
- **독립적 사용**: ChunkProcessor만으로 완전 수집 테스트
- **성능 회귀**: 메모리/시간 벤치마크 테스트
- **UI 연동**: Progress Callback 메커니즘 테스트

---

## ✅ Approval & Sign-off

### Review Checklist
- [ ] PRD 내용 검토 완료
- [ ] 기술적 타당성 검증 완료
- [ ] 리소스 할당 확인 완료
- [ ] 리스크 분석 검토 완료
- [ ] Timeline 검토 완료

### Stakeholder Approval
- [ ] **Tech Lead**: ChunkProcessor v2.0 설계 승인
- [ ] **Product Owner**: 비즈니스 가치 및 우선순위 승인
- [ ] **QA Lead**: 테스트 전략 및 검증 기준 승인

---

> **Next Action**: PRD 승인 후 `tasks/active/TASK_20250923_01-chunk_processor_v2_migration.md` 상세 태스크 문서로 진행

**PRD 버전**: v1.0
**최종 수정**: 2025년 9월 23일
**승인 대기중**: Tech Lead, Product Owner, QA Lead
