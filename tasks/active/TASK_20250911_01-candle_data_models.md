# 📋 TASK_01: 캔들 데이터 모델 정의

## 🎯 태스크 목표
- **주요 목표**: CandleDataProvider v4.0에 필요한 핵심 데이터 모델 3개 정의
- **완료 기준**:
  - RequestInfo: 요청 정보 표준화 모델 (@dataclass(frozen=True))
  - ChunkPlan: 청크 분할 계획 모델 (@dataclass(frozen=True))
  - ChunkInfo: 개별 청크 정보 모델 (@dataclass(frozen=False) - 실시간 조정 가능)
  - 모든 모델이 완벽한 타입힌트 적용

## 📊 현재 상황 분석
### 문제점
1. **데이터 모델 부재**: CandleDataProvider 구현에 필요한 표준화된 데이터 구조 없음
2. **파라미터 표준화 필요**: count, to, end 조합에 대한 일관된 표현 방식 필요
3. **청크 처리 정보 관리**: 분할된 청크들의 메타정보 체계적 관리 필요

### 사용 가능한 리소스
- ✅ **기존 CandleData 모델**: 업비트 API 호환 캔들 데이터 모델
- ✅ **TimeUtils**: 시간 변환 및 계산 유틸리티
- ✅ **업비트 API 스펙**: 공식 파라미터 조합 규칙
- ✅ **Python dataclass**: 불변 객체 생성 기능

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
### Phase 1: RequestInfo 모델 설계
- [ ] 4가지 파라미터 조합 지원 (count, count+to, to+end, end)
- [ ] 요청 타입 구분 (enum 또는 literal)
- [ ] 시간 범위 정규화 필드
- [ ] 검증 메서드 포함

### Phase 2: ChunkPlan 모델 설계
- [ ] 전체 청크 개수 및 크기 정보
- [ ] 각 청크의 시작/끝 시간 정보
- [ ] 총 예상 캔들 개수
- [ ] 청크 순서 및 우선순위

### Phase 3: ChunkInfo 모델 설계
- [ ] 개별 청크 식별 정보
- [ ] 청크별 파라미터 (count, to, end)
- [ ] 처리 상태 정보
- [ ] 이전/다음 청크와의 연결 정보
- [ ] 실시간 시간 조정 메서드 (adjust_times)

### Phase 4: 모델 검증 및 최적화
- [ ] 타입 힌트 완성도 검증
- [ ] Immutable 속성 확인 (RequestInfo, ChunkPlan만 frozen=True)
- [ ] ChunkInfo 수정 가능성 확인 (frozen=False, 실시간 조정용)
- [ ] 모델 간 호환성 테스트
- [ ] 메모리 효율성 확인

## 🛠️ 개발할 도구
- `candle_models.py`: RequestInfo, ChunkPlan, ChunkInfo 데이터 모델 (기존 파일 확장)

## 🎯 성공 기준
- ✅ RequestInfo: 모든 파라미터 조합 표준화 완료
- ✅ ChunkPlan: 청크 분할 계획 완전 표현 가능
- ✅ ChunkInfo: 개별 청크 메타정보 완전 관리 + 실시간 조정 기능
- ✅ RequestInfo, ChunkPlan은 @dataclass(frozen=True) + 완벽한 타입힌트
- ✅ ChunkInfo는 @dataclass(frozen=False) + 실시간 수정 가능성
- ✅ 모델 간 일관성 및 상호 호환성 보장

## 💡 작업 시 주의사항
### 설계 원칙
- **불변성**: RequestInfo, ChunkPlan은 @dataclass(frozen=True) 적용
- **수정 가능성**: ChunkInfo는 @dataclass(frozen=False) - 실시간 조정 필요
- **타입 안전성**: Optional, Union, Literal 등 정확한 타입힌트
- **검증**: 모델 생성 시 데이터 유효성 검증 로직 포함
- **확장성**: 향후 추가 기능을 고려한 유연한 구조

### 업비트 API 준수
- count: 1~200 범위 제한
- to/end: ISO 8601 형식 시간
- 파라미터 조합 규칙 정확히 반영

### 성능 고려사항
- 메모리 효율적 구조 (불필요한 필드 최소화)
- 빠른 객체 생성 (복잡한 초기화 로직 회피)
- 해시 가능한 구조 (RequestInfo, ChunkPlan은 캐시 키로 활용 가능)
- ChunkInfo 실시간 수정: 새 객체 생성 없이 기존 객체 수정으로 메모리 효율성 확보

## 🚀 즉시 시작할 작업
1. 기존 candle_models.py 파일 확인
2. 업비트 API 파라미터 조합 규칙 분석
3. RequestInfo 모델부터 설계 시작

```powershell
# 기존 모델 파일 확인
Get-Content upbit_auto_trading/infrastructure/market_data/candle/candle_models.py

# 업비트 API 스펙 확인
python -c "
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_public_client import UpbitPublicClient
import inspect
print('UpbitPublicClient 캔들 관련 메서드:')
for name, method in inspect.getmembers(UpbitPublicClient, predicate=inspect.ismethod):
    if 'candle' in name.lower():
        print(f'  - {name}')
"
```

---
**다음 에이전트 시작점**: Phase 1 - RequestInfo 모델 설계부터 시작
**후속 태스크**: TASK_02 (정규화+청크생성 로직)
