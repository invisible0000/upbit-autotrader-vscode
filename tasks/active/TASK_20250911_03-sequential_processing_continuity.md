# 📋 TASK_03: 청크 순차 처리 및 연속성 보장 메커니즘

## 🎯 태스크 목표
- **주요 목표**: 청크 순차 처리와 실시간 연속성 보장 시스템 구현
- **완료 기준**:
  - pr---
**다음 에이전트 시작점**: Phase 1 - process_chunks_sequentially 메서드부터 시작
**의존성**: TASK_02 (정규화+청크생성) 완료 필수
**후속 태스크**: TASK_04 (메인 API 구현)s_chunks_sequentially: 청크별 순차 처리 (병렬 아님)
  - adjust_chunk_based_on_previous: 이전 청크 결과 기반 다음 청크 조정
  - 연속성 보장 O(n) 효율성 달성 (기존 O(n²) 대비 최적화)
  - OverlapAnalyzer 완벽 연동

## 📊 현재 상황 분석
### 문제점
1. **연속성 보장 복잡성**: 이전 청크의 마지막 캔들과 다음 청크의 첫 캔들 간 연속성 검증 필요
2. **실시간 조정**: API 응답 결과에 따른 동적 청크 파라미터 조정 필요
3. **성능 최적화**: O(n²) → O(n) 효율성 개선 필요

### 사용 가능한 리소스
- ✅ **TASK_01 완성**: RequestInfo, ChunkPlan, ChunkInfo 데이터 모델
- ✅ **TASK_02 완성**: normalize_request, create_chunks 메서드
- ✅ **OverlapAnalyzer v5.0**: 5가지 상태 분류 (PERFECT, PARTIAL_OVERLAP, ADJACENT, GAP, DISJOINT)
- ✅ **CandleCache**: TTL/LRU 캐싱 시스템
- ✅ **UpbitPublicClient**: API 호출 및 Rate Limit 관리

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
### Phase 1: process_chunks_sequentially 메서드 구현
- [ ] 청크 순차 반복 처리 루프
- [ ] 각 청크별 UpbitPublicClient 호출
- [ ] API 응답을 CandleData 리스트로 변환
- [ ] 캐시 저장 및 조회 연동
- [ ] 에러 처리 및 재시도 로직

### Phase 2: adjust_chunk_based_on_previous 메서드 구현
- [ ] 이전 청크 결과 분석 (마지막 캔들 시간 확인)
- [ ] OverlapAnalyzer를 통한 연속성 상태 분석
- [ ] 다음 청크 파라미터 동적 조정 (to/end 시간 수정)
- [ ] ChunkInfo 업데이트 및 반환

### Phase 3: 연속성 보장 최적화
- [ ] O(n) 효율성 달성 알고리즘 구현
- [ ] 단일 패스(single-pass) 연속성 검증
- [ ] 메모리 효율적 임시 데이터 관리
- [ ] 불필요한 중복 계산 제거

### Phase 4: OverlapAnalyzer 연동 및 API 요청
- [ ] OverlapAnalyzer로 청크별 최적 API 요청 범위 획득
- [ ] 제공된 시작/끝 시간으로 UpbitPublicClient API 호출
- [ ] API 응답 데이터를 DB 저장 (자동 채워짐)
- [ ] 수집 결과를 다음 청크 연속성 조정에 활용

## 🛠️ 개발할 도구
- `candle_data_provider.py`: process_chunks_sequentially, adjust_chunk_based_on_previous 메서드

## 🎯 성공 기준
- ✅ process_chunks_sequentially: 모든 청크 순차 처리, API 응답 정확 변환
- ✅ adjust_chunk_based_on_previous: 실시간 청크 조정, 연속성 100% 보장
- ✅ O(n) 효율성 달성: 청크 수에 비례하는 선형 성능
- ✅ OverlapAnalyzer 연동: 최적 API 요청 범위 획득 및 활용
- ✅ 캐시 히트율 최적화: 중복 API 호출 최소화

## 💡 작업 시 주의사항
### 성능 최적화
- **순차 처리**: 병렬 처리하지 않고 순차적으로 (Rate Limit 준수)
- **메모리 관리**: 대량 캔들 데이터 처리 시 메모리 효율성 고려
- **캐시 활용**: CandleCache 적극 활용하여 중복 요청 방지
- **API 호출 최소화**: 필요한 경우에만 추가 요청

### 연속성 보장
- **정확한 시간 비교**: 나노초 단위까지 정확한 시간 비교
- **타임프레임 고려**: 각 타임프레임별 시간 간격 정확 적용
- **경계 조건**: 청크 경계에서의 정확한 연결 처리
- **데이터 무결성**: 중복/누락 없는 완전한 데이터 보장

### 에러 처리
- **네트워크 에러**: API 호출 실패 시 적절한 재시도
- **데이터 이상**: 예상과 다른 API 응답 처리
- **연속성 실패**: Gap 발견 시 적절한 대응 방안
- **Rate Limit**: 기존 시스템과 완벽 연동

## 🚀 즉시 시작할 작업
1. TASK_02 완성 상태 확인 (normalize_request, create_chunks)
2. OverlapAnalyzer 기본 연동 방식 분석
3. process_chunks_sequentially 기본 구조 생성

```powershell
# 이전 태스크 완성 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.candle_data_provider import CandleDataProvider
provider = CandleDataProvider()
print('✅ normalize_request 메서드:', hasattr(provider, 'normalize_request'))
print('✅ create_chunks 메서드:', hasattr(provider, 'create_chunks'))
"

# OverlapAnalyzer 상태 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer, OverlapStatus
print('✅ OverlapAnalyzer 기본 동작 확인')
print('  - analyze_overlap 메서드로 최적 API 요청 범위 제공')
print('  - API 호출 후 DB 자동 저장으로 겹침 해결')
"

# CandleCache 기능 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.candle_cache import CandleCache
cache = CandleCache()
print('✅ CandleCache 준비 완료')
print(f'  - 현재 캐시 크기: {len(cache._cache) if hasattr(cache, '_cache') else 'Unknown'}')
"
```

---
**다음 에이전트 시작점**: Phase 1 - process_chunks_sequentially 메서드 구현부터 시작
**의존성**: TASK_02 (정규화+청크생성) 완료 필수
**후속 태스크**: TASK_04 (메인 API 구현)
