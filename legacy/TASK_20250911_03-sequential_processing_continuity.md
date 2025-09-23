# 📋 TASK_03: 실제 API 호출 및 연속성 보장 구현

## 🎯 태스크 목표
- **주요 목표**: CandleDataProvider v4.0에 실제 API 호출, Repository 연동, 빈 캔들 처리 구현
- **완료 기준**:
  - 실제 UpbitPublicClient API 호출 로직 구현
  - Repository를 통한 DB 저장 및 조회 연동
  - OverlapAnalyzer 활용한 성능 최적화 구현
  - 빈 캔들 Merge 방식 통합 (docs/ideas/empty_candle_merge_implementation.md 기반)
  - 완전한 end-to-end 캔들 수집 시스템 완성

## 📊 현재 상황 분석 (2025-09-12 실제 확인 결과)
### 구현 완료 상태
- ✅ **CandleDataProvider v4.0**: 하이브리드 순차 처리 아키텍처 완성
  - plan_collection, start_collection, get_next_chunk, mark_chunk_completed
  - CollectionState 기반 실시간 상태 관리
  - 최소 사전 계획 + 실시간 청크 생성 방식
- ✅ **OverlapAnalyzer v5.0**: 5가지 상태 분류 완벽 구현
  - NO_OVERLAP, COMPLETE_OVERLAP, PARTIAL_START, PARTIAL_MIDDLE_FRAGMENT, PARTIAL_MIDDLE_CONTINUOUS
- ✅ **빈 캔들 Merge 설계**: 혁신적 전처리 패턴 완성

### 미완성 부분 (핵심 작업 대상)
- ❌ **Infrastructure 의존성**: Repository, UpbitPublicClient 연동 없음
- ❌ **실제 API 호출**: mark_chunk_completed가 가상 파라미터 처리만 함
- ❌ **DB 저장/조회**: Repository 통한 실제 데이터 처리 없음
- ❌ **빈 캔들 처리**: 설계는 완성, 실제 구현 연동 필요

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **[-] 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 수정된 작업 계획

### Phase 1: Infrastructure 의존성 연동 (새로 추가)
- [-] CandleDataProvider 생성자에 Repository 의존성 추가
- [ ] CandleDataProvider 생성자에 UpbitPublicClient 의존성 추가
- [ ] OverlapAnalyzer 인스턴스 생성 및 연동
- [ ] 의존성 주입 패턴으로 생성자 리팩터링
- [ ] 기본 연결 테스트 및 초기화 검증

### Phase 2: 실제 API 호출 시스템 구현 (핵심)
- [ ] `_fetch_chunk_from_api` 메서드 구현 (UpbitPublicClient 활용)
- [ ] `_convert_upbit_response_to_candles` 메서드 구현 (API → CandleData 변환)
- [ ] `mark_chunk_completed` 실제 구현 (가상 파라미터 → 실제 API 호출)
- [ ] API Rate Limit 준수 및 에러 처리 로직
- [ ] 실시간 청크 진행률 업데이트

### Phase 3: Repository 연동 및 데이터 저장 (필수)
- [ ] `_save_candles_to_repository` 메서드 구현
- [ ] Repository를 통한 기존 데이터 조회 로직
- [ ] 중복 저장 방지 및 데이터 무결성 보장
- [ ] 트랜잭션 기반 안전한 저장 처리
- [ ] 저장 성공/실패에 따른 상태 관리

### Phase 4: OverlapAnalyzer 활용 성능 최적화
- [ ] `_analyze_chunk_overlap` 메서드 구현 (청크별 겹침 분석)
- [ ] 5가지 상태별 최적 처리 로직 (DB only, API only, Mixed)
- [ ] COMPLETE_OVERLAP: 전체 DB 조회
- [ ] NO_OVERLAP: 전체 API 요청
- [ ] PARTIAL_*: 혼합 처리 (DB + API)

### Phase 5: 빈 캔들 처리 모듈 구현 (혁신적 기능)

#### 5.1: EmptyCandleProcessor 핵심 구현
- [ ] `empty_candle_processor.py` 새 파일 생성
- [ ] `EmptyCandleProcessor` 클래스 구현 (TimeUtils 의존성)
- [ ] `detect_empty_gaps(candles, timeframe)` → List[Tuple] (Gap 범위들)
- [ ] `generate_empty_candles_from_gaps(gaps, reference_candle)` → List[CandleData]
- [ ] `merge_and_sort_candles(real_candles, empty_candles)` → List[CandleData]

#### 5.2: 데이터 모델 확장
- [ ] CandleData에 `blank_copy_from_utc: Optional[str]` 필드 추가
- [ ] `to_db_dict()` 메서드 빈 캔들 지원 (NULL 최적화)
- [ ] `from_upbit_api()` 메서드는 기존 그대로 유지

#### 5.3: CandleDataProvider 통합
- [ ] EmptyCandleProcessor 인스턴스 생성 및 DI
- [ ] `mark_chunk_completed`에 빈 캔들 전처리 로직 통합
- [ ] Gap 감지 → 빈 캔들 생성 → Merge → Repository 저장 플로우
- [ ] 빈 캔들 개수 로깅 및 통계 추가

## 🛠️ 개발할 도구
- `candle_data_provider.py`: Infrastructure 의존성 연동 + 실제 API 호출 구현
- `empty_candle_processor.py`: 빈 캔들 Gap 감지 및 Merge 처리 전담 모듈 (🆕)
- `candle_models.py`: CandleData에 `blank_copy_from_utc` 필드 추가
- 새로운 메서드들: `_fetch_chunk_from_api`, `_analyze_chunk_overlap`, etc.
- 기존 메서드 확장: `mark_chunk_completed` 실제 구현 (API 호출 → 저장 → 빈 캔들 처리)

## 🎯 성공 기준
- ✅ **완전한 End-to-End 동작**: API 호출 → 데이터 변환 → DB 저장 → 상태 업데이트
- ✅ **OverlapAnalyzer 최적화**: 5가지 상태별 최적 처리 (DB/API 혼합)
- ✅ **빈 캔들 처리 통합**: 마이너 코인 1초봉 산발적 거래 완벽 지원
- ✅ **연속성 100% 보장**: 청크 간 Gap 없는 완전한 시계열 데이터
- ✅ **실제 동작 검증**: `python run_desktop_ui.py` → 캔들 수집 → DB 저장 확인

## 💡 작업 시 주의사항

### Infrastructure 연동
- **DDD 계층 준수**: Domain ← Infrastructure 의존성 역전 유지
- **의존성 주입**: 생성자 기반 깔끔한 의존성 관리
- **Infrastructure 로깅**: `create_component_logger("ComponentName")` 사용 필수
- **기존 아키텍처 보존**: 하이브리드 순차 처리의 장점 유지

### 실제 API 호출
- **Rate Limit 준수**: 업비트 10 RPS 제한 엄격 준수
- **에러 처리**: 네트워크 오류, 타임아웃, 4xx/5xx 응답 처리
- **데이터 변환**: 업비트 API 응답 → CandleData 정확한 매핑
- **순차 처리**: 병렬 요청 금지 (Rate Limit 보호)

### 빈 캔들 처리
- **NULL 최적화**: `blank_copy_from_utc` 필드만 설정, 나머지는 None
- **메모리 기반**: Gap 감지와 빈 캔들 생성은 메모리에서 고속 처리
- **Repository 투명**: 기존 저장 로직을 전혀 수정하지 않고 Merge 활용
- **저장 공간 절약**: 빈 캔들은 실제 캔들의 1/10 저장 공간만 사용

### 연속성 보장
- **시간 정확성**: ISO 8601 형식 정확한 파싱 및 TimeUtils 활용
- **청크 연결**: 이전 청크의 마지막 캔들 → 다음 청크의 시작점 연결
- **Gap 감지**: 업비트 응답 내 캔들들 사이의 빈 구간 정확 탐지
- **데이터 무결성**: 중복/누락 없는 완전한 시계열 보장

## 🚀 작업 진행 상황
1. **[x] CandleDataProvider 생성자 확장** - Repository, UpbitPublicClient, OverlapAnalyzer 의존성 주입 완료
2. **[-] 기본 Infrastructure 연결 테스트** - OverlapAnalyzer, Repository 인스턴스 생성 검증
3. **[ ] 첫 번째 실제 API 호출 메서드 구현** - `_fetch_chunk_from_api` 메서드 작성

```powershell
# 현재 상태 재확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
provider = CandleDataProvider()
print('✅ CandleDataProvider v4.0 로드 성공')
print('현재 구현된 메서드들:', [m for m in dir(provider) if not m.startswith('_')])
"

# OverlapAnalyzer 동작 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer, OverlapStatus
print('✅ OverlapAnalyzer 완전 구현 확인')
print('✅ 5가지 상태:', [status.value for status in OverlapStatus])
"

# 빈 캔들 설계 문서 확인
python -c "
import os
empty_candle_doc = 'd:/projects/upbit-autotrader-vscode/docs/ideas/empty_candle_merge_implementation.md'
print('✅ 빈 캔들 Merge 설계 문서:', os.path.exists(empty_candle_doc))
"
```

## 🆕 **EmptyCandleProcessor 설계 상세**

### **파일**: `empty_candle_processor.py`
```python
class EmptyCandleProcessor:
    """빈 캔들 Gap 감지 및 Merge 처리 전담 모듈"""

    def __init__(self, time_utils):
        self.time_utils = time_utils
        self.logger = create_component_logger("EmptyCandleProcessor")

    def detect_empty_gaps(self, candles: List[Dict], timeframe: str) -> List[Tuple]:
        """API 응답 캔들들 사이의 빈 구간 감지"""
        # docs/ideas/empty_candle_merge_implementation.md 알고리즘 구현

    def generate_empty_candles_from_gaps(self, gaps: List[Tuple], timeframe: str) -> List[CandleData]:
        """Gap 구간들에서 빈 캔들들 생성 (NULL 최적화)"""
        # blank_copy_from_utc만 설정, 나머지는 None

    def merge_and_sort_candles(self, real_candles: List[Dict], empty_candles: List[CandleData]) -> List[CandleData]:
        """실제 + 빈 캔들 병합 및 업비트 내림차순 정렬"""
        # Repository 투명 처리를 위한 완전 통합
```

### **CandleData 모델 확장**
```python
@dataclass
class CandleData:
    # 기존 필드들...
    blank_copy_from_utc: Optional[str] = None  # 빈 캔들 식별 필드

    def to_db_dict(self) -> dict:
        if self.blank_copy_from_utc is not None:
            # 빈 캔들: 2개 필드만 저장, 90% 공간 절약
            return {
                "candle_date_time_utc": self.candle_date_time_utc,
                "blank_copy_from_utc": self.blank_copy_from_utc
                # 나머지는 NULL
            }
        # 실제 캔들: 기존 로직 그대로
```

## 📋 **예상 구현 순서**
1. **Phase 1**: Infrastructure 의존성 (30분)
2. **Phase 2**: 실제 API 호출 (45분)
3. **Phase 3**: Repository 연동 (30분)
4. **Phase 4**: OverlapAnalyzer 최적화 (45분)
5. **Phase 5**: 빈 캔들 모듈 (75분)
   - 5.1: EmptyCandleProcessor (30분)
   - 5.2: 데이터 모델 확장 (15분)
   - 5.3: CandleDataProvider 통합 (30분)

**총 예상 시간**: 3.75시간 (완전한 end-to-end 캔들 수집 시스템)

---
**다음 에이전트 시작점**: Phase 1 - CandleDataProvider 생성자 확장부터 시작
**의존성**: 현재 CandleDataProvider v4.0 아키텍처 (✅ 완성)
**후속 태스크**: 완전한 시스템 테스트 및 최적화
