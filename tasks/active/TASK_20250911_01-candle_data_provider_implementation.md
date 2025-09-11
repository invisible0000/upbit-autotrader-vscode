# 📋 TASK_20250911_01: 캔들 데이터 제공자 v4.0 구현

## 🎯 태스크 목표
- **주요 목표**: 캔들 데이터 제공자 기능 기획_v2.md 기반으로 완전한 CandleDataProvider v4.0 구현
- **완료 기준**:
  - 모든 파라미터 조합(count, to, end) 지원
  - 청크 분할 및 순차 처리 메커니즘 구현
  - 실시간 연속성 보장 시스템 구현
  - 캔들 데이터 제공자 API가 정상적으로 동작

## 📊 현재 상황 분석
### 문제점
1. **CandleDataProvider 메인 로직 미구현**: 현재 백업 파일만 존재
2. **UpbitPublicClient API 연동 부족**: get_candles, get_candles_with_end 메서드 필요
3. **SqliteCandleRepository 미완성**: 3개 메서드 미구현 (get_latest_candle, get_table_stats, get_all_candle_tables)

### 사용 가능한 리소스
- ✅ **SqliteCandleRepository**: 13개 핵심 메서드 완전 구현
- ✅ **TimeUtils**: 6개 핵심 메서드 완전 구현
- ✅ **OverlapAnalyzer v5.0**: 완전 구현 (5가지 상태 분류)
- ✅ **CandleCache**: 완전 구현 (TTL, LRU 캐싱)
- ✅ **CandleData 모델**: 완전 구현 (업비트 API 호환)

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
### Phase 1: CandleDataProvider 메인 로직 구현
- [ ] RequestInfo, ChunkPlan, ChunkInfo 데이터 모델 정의
- [ ] 요청 정규화 메커니즘 구현 (normalize_request)
- [ ] 청크 생성 메커니즘 구현 (create_chunks)
- [ ] 청크 순차 처리 로직 구현 (process_chunks_sequentially)
- [ ] 실시간 연속성 보장 메커니즘 구현 (adjust_chunk_based_on_previous)

### Phase 2: UpbitPublicClient API 연동
- [ ] get_candles 메서드 구현 (기본 캔들 조회)
- [ ] get_candles_with_end 메서드 구현 (특정 시점까지 조회)
- [ ] API Rate Limit 처리 및 백오프 메커니즘
- [ ] API 응답을 CandleData 모델로 변환

### Phase 3: SqliteCandleRepository 완성
- [ ] get_latest_candle 메서드 구현 (캐시 확인용)
- [ ] get_table_stats 메서드 구현 (통계 정보)
- [ ] get_all_candle_tables 메서드 구현 (테이블 목록)

### Phase 4: 메인 get_candles API 구현
- [ ] 파라미터 검증 로직 구현
- [ ] 4가지 파라미터 조합 지원 (count, count+to, to+end, end)
- [ ] CandleDataResponse 생성 및 반환
- [ ] ProcessingStats 통계 정보 수집

### Phase 5: 최종 검증
- [ ] 기본 기능 동작 확인
- [ ] 각 파라미터 조합별 캔들 데이터 정상 조회 검증
- [ ] 성능 및 안정성 확인

## 🛠️ 개발할 도구
- `candle_data_provider.py`: 메인 캔들 데이터 Infrastructure Service
- `upbit_public_client.py`: 업비트 API 연동 클라이언트 (캔들 조회 메서드 추가)
- `candle_models.py`: RequestInfo, ChunkPlan, ChunkInfo 데이터 모델 추가

## 🎯 성공 기준
- ✅ 모든 파라미터 조합으로 캔들 데이터 정상 조회
- ✅ 청크 분할 시 실시간 연속성 보장 (O(n) 효율성)
- ✅ OverlapAnalyzer와 CandleCache 완벽 연동
- ✅ 캔들 데이터 제공자 API 완전 구현 및 정상 동작
- ✅ API Rate Limit 준수 및 안전한 에러 처리
- ✅ Infrastructure 로깅 시스템 활용

## 💡 작업 시 주의사항
### 안전성 원칙
- DDD 4계층 준수: Domain 순수성 유지, Infrastructure 격리
- 3-DB 분리: market_data.sqlite3만 사용
- Dry-Run 기본: 모든 주문 관련 기능은 dry_run=True 기본값
- API 키 보안: ApiKeyService 암호화 저장, 코드에 노출 금지

### 아키텍처 준수
- Infrastructure 로깅 필수: create_component_logger("CandleDataProvider")
- 에러 처리: 도메인 규칙 실패를 try/except로 숨기지 말 것
- 타입 힌트: DTO는 @dataclass(frozen=True) + 명확한 타입힌트

### 성능 최적화
- 청크 간 연속성 보장: O(n) 효율성 유지 (vs 기존 O(n²))
- 캐시 활용: CandleCache TTL/LRU 캐싱 최대한 활용
- DB 쿼리 최적화: SqliteCandleRepository 효율적 쿼리 패턴 활용

## 🚀 즉시 시작할 작업
1. 현재 캔들 데이터 제공자 구현 상태 확인
2. RequestInfo, ChunkPlan, ChunkInfo 데이터 모델 정의
3. CandleDataProvider 기본 구조 생성

```powershell
# 현재 상황 확인
Get-ChildItem upbit_auto_trading/infrastructure/market_data/candle -Name *.py

# 테스트 환경 확인
python -c "
from upbit_auto_trading.infrastructure.market_data.candle.candle_cache import CandleCache
from upbit_auto_trading.infrastructure.market_data.candle.overlap_analyzer import OverlapAnalyzer
print('✅ 기존 컴포넌트 로딩 확인 완료')
"
```

---
**다음 에이전트 시작점**: Phase 1 - CandleDataProvider 메인 로직 구현부터 시작
