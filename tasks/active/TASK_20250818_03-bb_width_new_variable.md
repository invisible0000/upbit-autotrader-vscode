# 📋 TASK_20250818_03: 볼린저 밴드 폭(BB_WIDTH) 신규 변수 추가

## 🎯 태스크 목표
- **주요 목표**: BB_WIDTH 신규 변수로 변동성 수축/확장 정밀 감지 시스템 구축
- **완료 기준**:
  - BB_WIDTH 독립 변수로 완전 구현 (절대값/백분율 정규화)
  - 1-2단계 모든 확장 기능 적용 (배율 + 통계 계산)
  - 기존 BOLLINGER_BAND와 조합 전략 가능

## 📊 현재 상황 분석
### 문제점
1. 기존 BOLLINGER_BAND는 상단/하단/중앙선만 제공
2. 밴드 폭 계산을 위해 두 값 동시 필요하지만 현재 시스템은 단일 값 반환
3. 변동성 수축(스퀴즈)/확장(익스팬션) 감지 도구 부재
4. 기존 변수 확장시 750+ 라인으로 LLM 처리 한계 초과

### 사용 가능한 리소스
- TASK_20250818_01,02 완료 후 배율 + 통계 계산 인프라
- 기존 BOLLINGER_BAND 계산 로직 (_calculate_bb_upper/lower)
- BOLLINGER_BAND_enhancement_design.md 설계 문서

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **⚡ 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🛠️ 작업 계획

### Phase 1: 신규 변수 기반 설계 (1일)
- [ ] BB_WIDTH 변수 메타데이터 정의
- [ ] tv_trading_variables 테이블에 BB_WIDTH 레코드 추가
- [ ] volatility_comparable 그룹에 분류
- [ ] 기존 BOLLINGER_BAND와 독립성 확인

### Phase 2: 전용 파라미터 구성 (1일)
- [ ] 기본 파라미터: period(20), std_dev(2.0), timeframe
- [ ] 정규화 파라미터: normalization (absolute/percentage)
- [ ] 1-2단계 확장: calculation_method, calculation_period, multiplier_percent
- [ ] 파라미터 UI 위젯 설계

### Phase 3: BB_WIDTH 전용 계산기 개발 (3일)
- [ ] BollingerBandWidthCalculator 클래스 구현 (370라인)
- [ ] 기본 밴드 폭 계산 로직 (상단 - 하단)
- [ ] 정규화 기능: 절대값 vs 백분율 (%BB Width)
- [ ] 통계 계산 기능 통합 (min/max/average/previous)
- [ ] 배율 적용 및 캐싱 최적화

### Phase 4: 정규화 기능 구현 (1일)
- [ ] 절대값 정규화: 밴드폭 원값 (KRW 단위)
- [ ] 백분율 정규화: (밴드폭 / 중앙선) * 100
- [ ] 정규화 방식별 UI 표시 및 단위 처리
- [ ] 정규화 변환 정확도 검증

### Phase 5: UI 통합 및 조합 전략 (2일)
- [ ] 트리거 빌더에서 BB_WIDTH 변수 선택 가능
- [ ] 정규화 콤보박스 UI 추가
- [ ] 기존 BOLLINGER_BAND와 조합 조건 테스트
- [ ] 변수 호환성 검증 (volatility_comparable 그룹)

### Phase 6: 혁신적 전략 구현 및 검증 (3일)
- [ ] 볼린저 스퀴즈 전략 구현
- [ ] 변동성 급증 감지 시스템
- [ ] 다중 변동성 분석 (ATR + BB_WIDTH)
- [ ] 7규칙 전략 통합 테스트

## 🛠️ 개발할 도구
- `bb_width_variable_creator.py`: BB_WIDTH 변수 완전 생성기
- `bb_width_calculator.py`: 밴드 폭 전용 계산기 (370라인)
- `normalization_converter.py`: 절대값↔백분율 변환 도구
- `squeeze_expansion_detector.py`: 스퀴즈/익스팬션 감지기

## 🎯 성공 기준
- ✅ BB_WIDTH 계산기 370라인 이하 (LLM 친화적)
- ✅ 절대값/백분율 정규화 정확도 99% 이상
- ✅ 1-2단계 모든 확장 기능 완벽 적용
- ✅ 기존 BOLLINGER_BAND 100% 호환성 유지
- ✅ 스퀴즈/익스팬션 감지 시나리오 완벽 구현
- ✅ 계산 성능 기존 BOLLINGER_BAND 대비 동일 수준

## 💡 작업 시 주의사항
### 안전성 원칙
- 기존 BOLLINGER_BAND 변수에 절대 영향 없음
- 신규 변수로 완전 독립 구현
- 기존 전략 호환성 100% 보장

### 설계 원칙
- 단일 책임: BB_WIDTH는 오직 밴드 폭만 담당
- LLM 친화적: 370라인 이하 엄격 준수
- 확장성: 1-2단계 모든 기능 자동 상속

### 성능 최적화
- 밴드 폭 계산 결과 캐싱
- 정규화 연산 최적화
- 메모리 효율적 히스토리 관리

## 🚀 즉시 시작할 작업
```sql
-- Step 1: BB_WIDTH 변수 추가
INSERT INTO tv_trading_variables (
    variable_id, display_name_ko, display_name_en,
    purpose_category, chart_category, comparison_group,
    description
) VALUES (
    'BB_WIDTH', '볼린저 밴드 폭', 'Bollinger Band Width',
    'volatility', 'subplot', 'volatility_comparable',
    '볼린저 밴드 상단과 하단 사이의 거리 (변동성 지표)'
);
```

## 📈 혁신적 활용 시나리오

### 볼린저 스퀴즈 전략
```yaml
진입 조건 1: BB_WIDTH < BB_WIDTH(20일최저, 110%)      # 극도 수축
진입 조건 2: CURRENT_PRICE < BOLLINGER_BAND[lower]    # 하단 터치
→ 스퀴즈 후 반등 강력한 신호
```

### 변동성 급증 감지
```yaml
출구 조건: BB_WIDTH > BB_WIDTH(5일평균, 150%)         # 밴드 급확장
→ 브레이크아웃 확인 후 수익 실현
```

### 다중 변동성 분석
```yaml
확인 조건 1: ATR(10일평균, 120%) < 현재값           # ATR 기준 수축
확인 조건 2: BB_WIDTH(15일최저, 110%) < 현재값      # 밴드폭 기준 수축
→ 이중 변동성 수축으로 폭발 임박 신호
```

### 정규화별 활용
```yaml
절대값 모드: BB_WIDTH > 50000  # KRW 단위 절대 기준
백분율 모드: BB_WIDTH > 8.0   # 중앙선 대비 8% 이상
```

## 🔗 다른 태스크와의 연관성
- **의존성**: TASK_20250818_01,02 완료 후 시작
- **연계 효과**: ATR과 BB_WIDTH 조합으로 변동성 분석 완전체
- **시너지**: HIGH_PRICE/LOW_PRICE와 조합으로 지지/저항 + 변동성 통합 분석

## 📊 예상 계산 복잡도
```python
# BB_WIDTH 계산 (370라인 예상)
class BollingerBandWidthCalculator:
    def _calculate_basic_width(self, data, period, std_dev):  # 130라인
        # 1. SMA 계산
        # 2. 표준편차 계산
        # 3. 상단/하단 계산
        # 4. 밴드 폭 = 상단 - 하단

    def _normalize_width(self, width, sma, method):           # 40라인
        # 절대값 vs 백분율 변환

    def _apply_statistical_method(self, width_series, params): # 150라인
        # min/max/average/previous 적용

    def _apply_multiplier(self, value, multiplier_percent):   # 20라인
        # 배율 적용

    def _cache_and_optimize(self, symbol, timeframe, result): # 30라인
        # 캐싱 및 최적화
```

---
**다음 에이전트 시작점**: BB_WIDTH 변수 메타데이터 등록 후 BollingerBandWidthCalculator 구현
**핵심 가치**: 변동성 수축/확장의 정밀한 감지로 7규칙 전략의 "급락/급등 감지" 규칙 완성
**최종 목표**: ATR + BB_WIDTH 조합으로 업비트 최고 수준의 변동성 분석 시스템 구축
