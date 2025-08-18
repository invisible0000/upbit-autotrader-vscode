# EXPL_MDMS스크리너시나리오01

**목적**: Market Data Management System 스크리너 사용 시나리오 분석
**대상**: 자산 스크리닝 → 매매 전략 → 백테스팅 → 실거래 플로우
**분량**: 197줄 / 200줄 (99% 사용)

---

## 🎯 **핵심 사용 시나리오 (1-20줄: 즉시 파악)**

### **사용자 플로우**
```
자산 스크리닝 → 매매 전략 관리 → 백테스팅 → 실거래 매매
     ↑              ↑              ↑          ↑
  MDMS 요청      MDMS 요청      MDMS 요청   MDMS 요청
```

### **스크리닝 시나리오 특성**
- **대량 심볼**: KRW 마켓 전체 (100+ 코인)
- **다양한 전략**: 단타/단기/스윙 동시 스크리닝
- **실시간 요구**: 즉시 결과 확인 필요
- **반복 사용**: 파라미터 변경하며 여러 번 실행

### **핵심 질문들**
1. **데이터 적재 시점**: 사전 vs 요청시점
2. **기간 확장 관리**: 7일→30일→60일 효율적 처리
3. **파편화 방지**: DB 무결성 유지 전략

---

## 📊 **시나리오 1: 최초 사용 (빈 DB) (21-60줄: 맥락)**

### **사용자 액션**
```yaml
스크리닝 설정:
- 대상: KRW 마켓 전체 (120개 코인)
- 타임프레임: 1일
- 기간: 7일
- 전략: 단타/단기/스윙 적합성 동시 검사

스크리닝 실행:
- "스크리닝 시작" 버튼 클릭
- 매매 변수 계산기 120개 코인 동시 계산 요청
```

### **MDMS 요청 패턴 분석**
```yaml
예상 요청량:
- 120개 심볼 × 1개 타임프레임 × 7일 = 840개 캔들
- 매매 변수별 중복 요청 가능성 높음
- ATR, RSI, MACD 등 동일 데이터 기반

실시간 요구사항:
- 사용자 대기시간: 최대 30초 허용
- 점진적 결과 표시: 10개씩 업데이트
- 진행률 표시: "45/120 완료"
```

### **전략 A: 사전 적재 (Preloading)**
```yaml
장점:
✅ 즉시 응답 가능 (1-2초)
✅ API Rate Limit 여유 확보
✅ 안정적인 사용자 경험

단점:
❌ 초기 적재 시간 (5-10분)
❌ 불필요한 데이터 적재 가능성
❌ 스토리지 사용량 증가

구현 방식:
- 백그라운드 스케줄러로 주요 심볼 선적재
- 사용자 설정 기반 필요 데이터 예측
- 점진적 적재 (우선순위 기반)
```

### **전략 B: 요청시 적재 (On-Demand)**
```yaml
장점:
✅ 필요한 데이터만 정확히 수집
✅ 스토리지 효율성 극대화
✅ 최신 데이터 보장

단점:
❌ 첫 실행시 긴 대기시간 (2-5분)
❌ API Rate Limit 부담
❌ 네트워크 의존성 높음

구현 방식:
- 실시간 병렬 수집 (최대 10개 동시)
- 진행률 UI 제공
- 캐시 활용한 점진적 최적화
```

---

## 🔄 **시나리오 2: 기간 확장 (7일→30일) (61-120줄: 상세)**

### **사용자 액션 (당일 재사용)**
```yaml
기존 설정:
- 대상: KRW 마켓 전체
- 타임프레임: 1일
- 기간: 7일 (이미 수집됨)

변경 설정:
- 기간: 30일 (23일 추가 필요)
- 나머지 동일
```

### **데이터 상태 분석**
```yaml
DB 현재 상태:
- KRW-BTC: 1일 캔들 7개 (최신 7일)
- KRW-ETH: 1일 캔들 7개 (최신 7일)
- ... (120개 심볼 동일)

추가 필요 데이터:
- 각 심볼당 23일 과거 데이터
- 총 23 × 120 = 2,760개 캔들
```

### **파편화 방지 전략**
```yaml
문제점:
❌ 7일 데이터와 30일 데이터가 분리 저장
❌ 동일 심볼의 타임스탬프 불연속성
❌ 쿼리 복잡도 증가

해결 방안:
✅ 연속성 보장 저장 (Gap-Free Storage)
✅ 타임스탬프 기반 정렬 삽입
✅ 중복 방지 Upsert 전략
```

### **효율적 확장 알고리즘**
```python
class DataExtensionManager:
    def extend_timeframe_data(self, symbol: str, current_days: int, target_days: int):
        """기간 확장시 효율적 데이터 추가"""

        # 1. 현재 데이터 범위 확인
        existing_range = self.get_data_range(symbol, "1d")

        # 2. 필요한 추가 범위 계산
        needed_start = existing_range.start - timedelta(days=target_days-current_days)

        # 3. Gap 없는 연속 데이터 요청
        missing_data = self.fetch_missing_range(symbol, needed_start, existing_range.start)

        # 4. 원자성 보장 삽입
        with self.db.transaction():
            self.insert_with_gap_filling(symbol, missing_data)

        return self.get_continuous_data(symbol, "1d", target_days)
```

### **성능 최적화 전략**
```yaml
병렬 처리:
- 심볼별 독립 확장 (120개 동시)
- 타임프레임별 배치 요청
- API Rate Limit 분산

캐시 활용:
- 기존 7일 데이터 메모리 유지
- 새 23일 데이터 점진적 추가
- 전체 30일 통합 캐시 생성

사용자 경험:
- 기존 7일 결과 즉시 표시
- 확장 데이터 점진적 업데이트
- "30일 데이터 수집 중... 23/120"
```

---

## 📈 **시나리오 3: 양방향 확장 (30일→60일) (121-180줄: 실행)**

### **1주일 후 사용자 액션**
```yaml
기존 데이터 (1주일 전 수집):
- 각 심볼: 30일 데이터 (Day -30 ~ Day -1)
- 현재 시점: Day 0 (1주일 지남)

새 요청:
- 60일 데이터 필요
- 과거 30일 + 최근 7일 추가 필요
```

### **복합 데이터 갭 상황**
```yaml
데이터 갭 분석:
Past Gap: Day -60 ~ Day -30 (30일, 과거 확장)
Current Gap: Day -1 ~ Day 6 (7일, 최신 업데이트)

DB 상태:
[Gap 30일] [기존 30일] [Gap 7일] [현재]
Day-60    Day-30    Day-1    Day6
```

### **양방향 확장 알고리즘**
```python
class BidirectionalExtensionManager:
    def extend_both_directions(self, symbol: str, target_days: int):
        """과거/현재 양방향 데이터 확장"""

        # 1. 현재 데이터 범위 분석
        existing_data = self.analyze_existing_data(symbol)
        current_range = existing_data.get_continuous_range()

        # 2. 필요한 갭 계산
        past_gap = self.calculate_past_gap(current_range, target_days)
        future_gap = self.calculate_future_gap(current_range)

        # 3. 병렬 수집 계획
        collection_plan = [
            DataRequest(symbol, past_gap.start, past_gap.end, priority="low"),
            DataRequest(symbol, future_gap.start, future_gap.end, priority="high")
        ]

        # 4. 우선순위 기반 수집
        for request in sorted(collection_plan, key=lambda x: x.priority):
            await self.collect_and_merge(request)

        return self.get_unified_data(symbol, target_days)
```

### **데이터 무결성 보장**
```yaml
원자성 보장:
- 전체 확장을 단일 트랜잭션으로 처리
- 실패시 기존 데이터 보존
- 부분 실패 복구 전략

일관성 검증:
- 타임스탬프 연속성 체크
- 중복 데이터 제거
- 누락 구간 식별 및 재수집

격리성 유지:
- 다른 사용자 요청과 독립 처리
- 동시 접근 시 Lock 관리
- Read-While-Write 지원
```

### **사용자 경험 최적화**
```yaml
점진적 업데이트:
Phase 1: 기존 30일 즉시 표시 (0초)
Phase 2: 최근 7일 추가 (10초)
Phase 3: 과거 30일 추가 (30초)

실시간 피드백:
- "60일 데이터 구성 중..."
- "최신 데이터 수집: 7/7 완료"
- "과거 데이터 수집: 15/30 완료"
- "60일 스크리닝 준비 완료"
```

---

## 💡 **MDMS 핵심 기능 도출 (181-197줄: 연결)**

### **필수 기능 요구사항**
```yaml
1. 적응적 데이터 수집:
   - 사전 vs 요청시 하이브리드
   - 사용 패턴 학습 기반 예측

2. 갭 없는 확장:
   - 양방향 데이터 확장 지원
   - 원자성 보장 삽입/업데이트

3. 효율적 스토리지:
   - 중복 제거 및 압축
   - 파편화 방지 정책

4. 실시간 피드백:
   - 점진적 결과 업데이트
   - 명확한 진행률 표시
```

### **다음 문서 계획**
- `EXPL_MDMS스크리너시나리오02.md` - 매매 전략 단계 시나리오
- `EXPL_MDMS백테스팅시나리오03.md` - 백테스팅 데이터 요구사항
- `PLAN_MDMS아키텍처v1.md` - 시나리오 기반 아키텍처 설계

**결론**: 스크리너 시나리오만으로도 MDMS의 **핵심 복잡성**이 드러남 🎯
