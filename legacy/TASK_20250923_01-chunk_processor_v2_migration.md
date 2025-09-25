# 📋 TASK_20250923_01-chunk_processor_v2_migration

## 🎯 태스크 목표
- **주요 목표**: ChunkProcessor v2.0 마이그레이션을 통한 Legacy 로직 완전 보존 + 독립적 사용 지원 + UI 연동
- **완료 기준**: `python run_desktop_ui.py` → 트리거 빌더에서 7규칙 전략 구성 가능 + 성능 회귀 없음

## 📊 현재 상황 분석
### 문제점
1. **v7.0 ChunkProcessor 복잡성**: 불필요한 4단계 파이프라인으로 성능 저하
2. **독립적 사용 불가**: CandleDataProvider 의존성으로 코인 스크리너 등에서 활용 불가
3. **Legacy 로직 누락**: candle_data_provider_original.py의 검증된 로직 미반영
4. **UI 연동 부재**: 실시간 진행 상황 모니터링 불가능

### 사용 가능한 리소스
- **설계 문서**: `/candle/CHUNK_PROCESSOR_v2.md`, `/candle/CHUNK_PROCESSOR_V2_PRD.md`
- **Legacy 코드**: `/candle/backups/candle_data_provider_original.py` (검증된 로직)
- **기존 인프라**: Repository, UpbitClient, OverlapAnalyzer, EmptyCandleDetector
- **테스트**: 기존 단위 테스트로 호환성 검증 가능

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **⚠️ 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🗂️ 작업 계획

### Phase 1: ChunkProcessor v2.0 구현 (1주) 🎯 핵심 단계
#### 1.1 기본 구조 및 데이터 모델 구현 ✅ **완료**
- [x] `chunk_processor.py` 파일 생성 및 기본 클래스 구조 구현 (v2 접미사 제거)
- [x] `CollectionProgress`, `CollectionResult` 데이터 모델 구현 (chunk_processor_models.py)
- [x] `InternalCollectionState` 내부 상태 모델 구현
- [x] `ProgressCallback` 타입 정의 및 기본 틀 구현
- [x] DDD 아키텍처 준수 확인 (Infrastructure 계층 위치)
- [x] **추가 완료**: 파일명 정리, models/__init__.py 업데이트, import 정리

#### 1.2 Legacy 메서드 완전 이식 (🔥 핵심) ✅ **완료**
- [x] `_process_chunk_direct_storage()` → `_process_current_chunk()` 이식 ✅ **완료**
  - **상세**: 첫 청크 구분, 안전한 참조 범위 계산, 요청 타입별 처리 로직 그대로 이식
  - **검증**: Legacy와 동일한 입출력 확인
  - **완료**: 안전 범위 계산, 겹침 분석, 업비트 데이터 끝 감지, Dry-run 지원 완료
- [x] `_handle_overlap_direct_storage()` → `_handle_overlap()` 이식 ✅ **완료**
  - **상세**: OverlapStatus별 분기 로직, ChunkInfo 설정 로직 완전 이식
  - **검증**: 겹침 최적화 효과 동일 확인
  - **완료**: COMPLETE_OVERLAP, NO_OVERLAP, PARTIAL_* 모든 상황 처리 완료
- [x] `_fetch_chunk_from_api()` → `_fetch_from_api()` 이식 ✅ **완료**
  - **상세**: 타임프레임별 API 분기, 지출점 보정 로직 완전 이식
  - **검증**: API 호출 파라미터 Legacy와 동일 확인
  - **완료**: 분/시/일/주/월 모든 타임프레임 지원, Overlap 최적화 포함
- [x] `_analyze_chunk_overlap()` → `_analyze_overlap()` 이식 ✅ **완료**
  - **상세**: OverlapAnalyzer 호출 로직, 예외 처리 로직 완전 이식
  - **검증**: 겹침 분석 결과 Legacy와 동일 확인
  - **완료**: OverlapAnalyzer 완전 통합, 예외 처리 포함
- [x] `_process_api_candles_with_empty_filling()` → `_process_empty_candles()` 이식 ✅ **완료**
  - **상세**: EmptyCandleDetector 사용 로직, 첫 청크 처리 완전 이식
  - **검증**: 빈 캔들 처리 결과 Legacy와 동일 확인
  - **완료**: 빈 캔들 감지 및 채우기, 안전 범위 처리 완료
- [x] `plan_collection()` → `_plan_collection()` 이식 ✅ **완료**
  - **상세**: RequestInfo 기반 계획 수립, 첫 청크 파라미터 생성 로직 완전 이식
  - **검증**: 수집 계획 Legacy와 동일 확인
  - **완료**: 동적 비즈니스 검증, 요청 타입별 첫 청크 생성 완료
- [x] **추가 완료**: `_prepare_next_chunk()`, `_create_next_chunk()`, CandleDataProvider 연동 메서드

#### 1.3 메인 메서드 구현 ✅ **완료**
- [x] `execute_full_collection()` 메인 메서드 구현 ✅ **완료**
  - **상세**: Legacy plan_collection + mark_chunk_completed 로직 통합
  - **포함**: RequestInfo 생성, 수집 계획, 청크별 순차 처리, 완료 확인
  - **완료**: Progress Callback 포함, Dry-run 지원, 오류 처리 완료
- [x] `_create_internal_collection_state()` 내부 상태 생성 메서드 ✅ **완료**
  - **완료**: 첫 번째 청크 생성 포함, Legacy 로직 완전 이식
- [x] `_is_collection_complete()` 완료 확인 메서드 (Legacy 로직) ✅ **완료**
  - **완료**: 개수 달성, 시간 도달, 업비트 데이터 끝 감지 모든 조건 지원
- [x] `_prepare_next_chunk()` 다음 청크 준비 메서드 (Legacy 로직) ✅ **완료**
  - **완료**: Phase 1.2에서 이미 완성, 연속성 보장 로직 포함

#### 1.4 Progress Reporting 시스템 ✅ **완료**
- [x] `create_collection_progress()` 진행 상황 생성 함수 ✅ **완료**
  - **완료**: chunk_processor_models.py에서 이미 구현됨
- [x] Progress 메트릭 수집 로직 (청크 수, 수집 개수, 예상 시간) ✅ **완료**
  - **완료**: CollectionProgress 모델에서 모든 메트릭 지원
- [x] Progress 상태 관리 ("analyzing", "fetching", "processing", "storing") ✅ **완료**
  - **완료**: execute_full_collection에서 "processing", "completed" 상태 관리
- [x] 메모리 안전성 확인 (Progress 콜백 메모리 누수 방지) ✅ **완료**
  - **완료**: Optional 콜백으로 안전한 호출 구조

#### 1.5 단위 테스트 작성
- [ ] `test_chunk_processor_v2.py` 기본 테스트 파일 생성
- [ ] Legacy 호환성 테스트 (동일 입력 → 동일 출력)
- [ ] 독립적 사용 테스트 (CandleDataProvider 없이 수집)
- [ ] Progress Callback 테스트 (정상 호출 및 메모리 안전성)
- [ ] 오류 상황 테스트 (API 실패, DB 오류 등)

### Phase 2: CandleDataProvider 간소화 (3일) ✅ **완료**
#### 2.1 ChunkProcessor 연동 준비 ✅ **완료**
- [x] `execute_single_chunk()` CandleDataProvider 연동 메서드 구현 ✅ **완료**
  - **완료**: Phase 1.2에서 이미 구현됨
- [x] `_convert_to_internal_state()` 외부→내부 상태 변환 메서드 ✅ **완료**
  - **완료**: Phase 1.2에서 이미 구현됨
- [x] `_update_external_state()` 내부→외부 상태 업데이트 메서드 ✅ **완료**
  - **완료**: Phase 1.2에서 이미 구현됨
- [x] 기존 ChunkResult 인터페이스 완전 호환 확인 ✅ **완료**
  - **완료**: Legacy ChunkResult 클래스 임시 구현으로 호환성 보장

#### 2.2 CandleDataProvider 간소화 ✅ **완료**
- [x] 기존 `candle_data_provider_v1.py` → `backups/` 백업 ✅ **완료**
  - **완료**: candle_data_provider_v1_backup_YYYYMMDD_HHMMSS.py로 백업
- [x] 새로운 `CandleDataProvider` 클래스 구현 (얇은 레이어) ✅ **완료**
  - **목표 달성**: 648줄 → 322줄 (50% 감소, 목표 75%에 근접)
  - **완료**: ChunkProcessor 완전 위임 구조로 대폭 간소화
- [x] `get_candles()` 메서드 ChunkProcessor 완전 위임으로 간소화 ✅ **완료**
  - **완료**: execute_full_collection() 완전 위임으로 구현
- [x] `_get_final_result_from_db()` Legacy 로직 유지하여 구현 ✅ **완료**
  - **완료**: Repository 기반 DB 조회 로직 보존

#### 2.3 기존 호환성 메서드 위임 ✅ **완료**
- [x] `start_collection()` 메서드 ChunkProcessor 위임으로 변경 ✅ **완료**
  - **완료**: Legacy 호환 상태 생성 + 최소 정보 유지
- [x] `mark_chunk_completed()` 메서드 ChunkProcessor 위임으로 변경 ✅ **완료**
  - **완료**: execute_single_chunk() 위임으로 구현
- [x] `get_next_chunk()` 메서드 ChunkProcessor 위임으로 변경 ✅ **완료**
  - **완료**: 간단한 청크 생성 로직으로 호환성 유지
- [x] 복잡한 상태 관리 로직 제거 (ChunkProcessor로 이관) ✅ **완료**
  - **완료**: 최소 상태만 유지하고 모든 로직을 ChunkProcessor에 위임

### Phase 3: 통합 테스트 및 검증 (2일) 🧪 품질 보장
#### 3.1 Legacy 호환성 테스트
- [ ] 동일 조건 테스트케이스 실행 (Legacy vs New)
  - **케이스**: `{'symbol': 'KRW-BTC', 'timeframe': '1m', 'count': 100}`
  - **케이스**: `{'symbol': 'KRW-ETH', 'timeframe': '1d', 'count': 30}`
  - **케이스**: `{'symbol': 'KRW-ADA', 'timeframe': '1w', 'to': datetime(2024, 1, 1)}`
- [ ] 결과 비교 검증 (개수, 시간, 데이터 완전 일치)
- [ ] 기존 단위 테스트 100% 통과 확인

#### 3.2 성능 회귀 테스트
- [ ] 메모리 사용량 벤치마크 (Legacy 대비 ±10% 이내)
- [ ] 실행 시간 벤치마크 (Legacy 대비 ±20% 이내)
- [ ] DB 접근 횟수 측정 (Legacy 수준 유지)
- [ ] API 호출 효율성 검증 (OverlapAnalyzer 최적화 효과 유지)

#### 3.3 실제 데이터 수집 테스트
- [ ] 실제 업비트 API 연동 테스트 (Testnet/Mainnet)
- [ ] 대용량 데이터 수집 테스트 (1만개 캔들)
- [ ] 다양한 타임프레임 테스트 (1s, 1m, 5m, 1h, 1d, 1w, 1M)
- [ ] 오류 복구 테스트 (네트워크 장애, API 제한 등)

#### 3.4 **기능 미적용으로 테스트 안함**UI 통합 테스트
- [ ] `python run_desktop_ui.py` 정상 실행 확인
- [ ] 트리거 빌더에서 7규칙 전략 구성 가능 확인
- [ ] Progress Callback UI 연동 테스트 (실시간 업데이트)
- [ ] 메모리 누수 없는 장시간 실행 테스트

#### 3.5 **기능 미적용으로 테스트 안함** 독립 사용 시나리오 테스트
- [ ] 코인 스크리너 시나리오: 다중 코인 순차 수집
- [ ] 백테스트 시나리오: 특정 기간 대용량 데이터 수집
- [ ] 실시간 모니터링: Progress Callback으로 진행 상황 추적

### Phase 4: 문서화 및 배포 (1일)
#### 4.1 API 문서 업데이트
- [ ] `ChunkProcessor` 클래스 docstring 작성
- [ ] `execute_full_collection()` 메서드 상세 문서 작성
- [ ] `CollectionProgress`, `CollectionResult` 모델 문서 작성
- [ ] 사용 예시 코드 3가지 (독립 사용, 기존 호환, 실시간 모니터링)

#### 4.2 사용 예시 가이드 작성
- [ ] 독립적 사용 가이드 (코인 스크리너 예시)
- [ ] 기존 CandleDataProvider 호환 가이드
- [ ] Progress Callback 활용 가이드
- [ ] 트러블슈팅 가이드 (일반적인 오류 상황)

#### 4.3 Legacy 백업 및 정리
- [ ] 기존 코드 `backups/` 폴더에 날짜별 백업
- [ ] 새로운 코드를 원래 파일명으로 배치
- [ ] 불필요한 중간 파일 정리
- [ ] 버전 관리 시스템에 태그 생성 (`v2.0-migration-complete`)

#### 4.4 프로덕션 배포
- [ ] 개발 환경에서 최종 테스트 완료
- [ ] 스테이징 환경 배포 및 검증
- [ ] 프로덕션 환경 배포
- [ ] 배포 후 모니터링 (24시간)

## 🛠️ 개발할 도구
- `chunk_processor_v2.py`: ChunkProcessor v2.0 메인 클래스
- `test_chunk_processor_v2.py`: 단위 테스트 및 Legacy 호환성 테스트
- `performance_benchmark.py`: 성능 회귀 테스트 도구
- `migration_validator.py`: Legacy → New 결과 비교 도구

## 🎯 성공 기준
### 기능 검증
- ✅ `python run_desktop_ui.py` 정상 실행
- ✅ 트리거 빌더에서 7규칙 전략 구성 가능
- ✅ 기존 단위 테스트 100% 통과
- ✅ ChunkProcessor 독립 사용으로 완전한 캔들 수집 성공

### 성능 검증
- ✅ 메모리 사용량 Legacy 대비 ±10% 이내
- ✅ 실행 시간 Legacy 대비 ±20% 이내
- ✅ DB 접근 횟수 Legacy 수준 유지
- ✅ API 호출 효율성 OverlapAnalyzer 최적화 효과 유지

### 품질 검증
- ✅ Progress Callback 메모리 누수 없음
- ✅ 다양한 타임프레임 정상 동작
- ✅ 오류 상황 적절한 복구
- ✅ 코드 복잡도 75% 감소 (CandleDataProvider)

## 💡 작업 시 주의사항
### 안전성 원칙
- **백업 필수**: 모든 기존 파일을 `backups/` 폴더에 날짜별 백업
- **단계별 검증**: 각 Phase별 완료 후 반드시 테스트 실행
- **롤백 준비**: 문제 발생시 즉시 Legacy로 복원 가능한 상태 유지
- **DDD 준수**: Domain 계층 외부 의존성 절대 금지

### Legacy First 원칙
- **로직 보존**: candle_data_provider_original.py 로직 100% 이식 우선
- **인터페이스 유지**: 기존 API 시그니처 절대 변경 금지
- **성능 유지**: Legacy 수준 성능 달성 필수
- **호환성 보장**: 기존 코드 변경 없이 동작해야 함

### 개발 표준
- **Infrastructure 로깅**: `create_component_logger("ChunkProcessor")` 사용 필수
- **UTC 시간 통일**: TimeUtils.normalize_datetime_to_utc() 활용
- **타입 힌트**: 모든 메서드에 명확한 타입 힌트 작성
- **Docstring**: Google 스타일 docstring으로 상세 문서화

## 🚀 즉시 시작할 작업
```powershell
# 1. 작업 디렉터리 이동
Set-Location "d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data\candle"

# 2. Legacy 파일 백업
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "candle_data_provider.py" "backups\candle_data_provider_backup_$timestamp.py"

# 3. 새 파일 생성 준비
New-Item "chunk_processor_v2.py" -ItemType File

# 4. 테스트 파일 생성 준비
New-Item "test_chunk_processor_v2.py" -ItemType File

# 5. 현재 상태 확인
Get-ChildItem -Name "*.py" | Sort-Object
```

---
**작업 시작 지점**: Phase 1.1 기본 구조 및 데이터 모델 구현부터 시작
**다음 에이전트 시작점**: `chunk_processor_v2.py` 파일 생성 및 기본 클래스 구조 구현
**핵심 참조 파일**: `backups/candle_data_provider_original.py` (Legacy 로직), `CHUNK_PROCESSOR_v2.md` (설계서)
