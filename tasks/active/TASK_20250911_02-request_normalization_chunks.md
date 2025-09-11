# 📋 TASK_02: 요청 정규화 및 청크 생성 로직

## 🎯 태스크 목표
- **주요 목표**: CandleDataProvider의 핵심 로직인 요청 정규화와 청크 생성 메커니즘 구현
- **완료 기준**:
  - normalize_request: 모든 파라미터 조합을 표준 형태로 변환
  - create_chunks: 대량 요청을 최적 크기로 분할
  - 업비트 API 제약사항 완벽 준수 (count 1~200, 파라미터 조합 규칙)

## 📊 현재 상황 분석
### 문제점
1. **파라미터 조합 복잡성**: count, count+to, to+end, end 4가지 조합 각각 다른 처리 필요
2. **청크 크기 최적화**: API 제한(200개)과 성능을 고려한 최적 분할 필요
3. **시간 범위 계산**: 타임프레임별 정확한 시간 간격 계산 필요

### 사용 가능한 리소스
- ✅ **TASK_01 완성**: RequestInfo, ChunkPlan, ChunkInfo 데이터 모델
- ✅ **TimeUtils**: 시간 변환 및 계산 유틸리티 (6개 메서드)
- ✅ **업비트 API 스펙**: 공식 파라미터 제약사항
- ✅ **기존 OverlapAnalyzer**: 시간 범위 분석 기능

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

## ⚙️ 작업 계획
### Phase 1: normalize_request 메서드 구현
- [ ] 4가지 파라미터 조합 검증 로직
- [ ] 누락된 시간 범위 계산 (count → to/end 변환)
- [ ] 파라미터 유효성 검증 (count 1~200, 시간 형식)
- [ ] RequestInfo 객체 생성 및 반환

### Phase 2: create_chunks 메서드 구현
- [ ] 전체 요청 크기 분석 (예상 캔들 개수 계산)
- [ ] 200개 단위 고정 청크 분할 (업비트 API 최대 제한 활용)
- [ ] 시간 범위별 청크 분할 알고리즘
- [ ] ChunkPlan 및 ChunkInfo 리스트 생성

### Phase 3: TimeUtils 활용 및 엣지 케이스 검증
- [ ] TimeUtils 메서드 활용 검증 (기존 구현 활용)
- [ ] 엣지 케이스 테스트 (월말, 연말, 타임프레임 경계)
- [ ] 시간 범위 경계 처리 정확성 확인
- [ ] 청크 간 시간 연속성 검증

### Phase 4: 검증 및 테스트
- [ ] 각 파라미터 조합별 기본 테스트 케이스
- [ ] 청크 분할 정확성 검증
- [ ] TimeUtils 엣지 케이스 동작 확인
- [ ] 에러 처리 강화

## 🛠️ 개발할 도구
- `candle_data_provider.py`: normalize_request, create_chunks 메서드 구현

## 🎯 성공 기준
- ✅ normalize_request: 모든 파라미터 조합 정확 처리, RequestInfo 완벽 생성
- ✅ create_chunks: 200개 단위 고정 분할, ChunkPlan 정확 생성
- ✅ 업비트 API 제약사항 100% 준수 (count 1~200, 파라미터 조합)
- ✅ 타임프레임별 정확한 시간 계산 (정밀도 1초 이내)
- ✅ OverlapAnalyzer 연동으로 자동 최적화 (API 호출 최소화)

## 💡 작업 시 주의사항
### API 제약사항 준수
- **count**: 1~200 범위 엄격 준수
- **파라미터 조합**: 업비트 API 공식 규칙 정확 구현
- **시간 형식**: ISO 8601 (YYYY-MM-DDTHH:mm:ss) 정확 사용
- **Rate Limit**: 기존 시스템 활용, 추가 부하 최소화

### 성능 최적화
- **청크 크기**: 200개 고정 (업비트 API 최대 제한 활용)
- **기존 TimeUtils 활용**: 완전 구현된 시간 계산 메서드 활용
- **메모리 효율**: 대량 청크 생성 시 메모리 사용량 최적화
- **자동 최적화**: OverlapAnalyzer가 실제 API 호출 최적화 담당

### 정확성 보장
- **TimeUtils 활용**: 완전 구현된 시간 계산 메서드 활용
- **엣지 케이스**: 월말, 연말, 타임프레임 경계 등 특수 상황 테스트
- **데이터 일관성**: 청크 간 중복/누락 방지

## 🚀 즉시 시작할 작업
1. TASK_01 완성 상태 확인 (RequestInfo, ChunkPlan, ChunkInfo 모델)
2. 업비트 API 파라미터 조합 규칙 상세 분석
3. normalize_request 메서드 기본 구조 생성

```powershell
# 데이터 모델 완성 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.candle_models import RequestInfo, ChunkPlan, ChunkInfo
print('✅ 데이터 모델 로딩 성공')
print(f'RequestInfo 필드: {RequestInfo.__dataclass_fields__.keys()}')
print(f'ChunkPlan 필드: {ChunkPlan.__dataclass_fields__.keys()}')
print(f'ChunkInfo 필드: {ChunkInfo.__dataclass_fields__.keys()}')
"

# TimeUtils 기능 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils
print('✅ TimeUtils 사용 가능 메서드:')
for method in dir(TimeUtils):
    if not method.startswith('_'):
        print(f'  - {method}')
"
```

---
**다음 에이전트 시작점**: Phase 1 - normalize_request 메서드 구현부터 시작
**의존성**: TASK_01 (데이터 모델) 완료 필수
**후속 태스크**: TASK_03 (순차처리+연속성 로직)
