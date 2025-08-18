# EXPL_MDMS매매전략시나리오02

**목적**: 매매 전략 단계에서의 MDMS 실시간 처리 요구사항 분석
**대상**: 스크리너 → **매매 전략** → 백테스팅 → 실거래 플로우
**분량**: 199줄 / 200줄 (100% 사용)

---

## 🎯 **매매 전략 시나리오 특성 (1-20줄: 즉시 파악)**

### **스크리너와의 차이점**
```yaml
스크리너: 대량 배치 처리 (120개 심볼 동시)
매매전략: 실시간 단일 처리 (1-3개 심볼 집중)

스크리너: 변동성/추세성 간단 지표
매매전략: 복합 규칙 + 7규칙 전략 엔진

스크리너: 30초 대기 허용
매매전략: 1-2초 즉시 응답 필수
```

### **핵심 요구사항**
- **즉시성**: 시장 변화에 실시간 대응
- **정확성**: 7규칙 전략 완벽 동작
- **연속성**: 계속된 모니터링 및 신호 생성
- **안정성**: 매매 중단 없는 무중단 서비스

### **복잡성 증가 요인**
- **7규칙 상호작용**: RSI과매도 + 불타기 + 트레일링스탑 조합
- **실시간 업데이트**: 새 캔들 생성시 모든 지표 재계산
- **상태 관리**: 진입/보유/청산 상태별 다른 계산 로직

---

## 🔄 **시나리오 1: 전략 활성화 (21-60줄: 맥락)**

### **사용자 액션**
```yaml
전략 설정:
- 심볼: KRW-BTC (스크리너에서 선정)
- 타임프레임: 15분
- 7규칙 활성화:
  * RSI 과매도 진입 (RSI < 30)
  * 수익시 불타기 (수익률 > 2%)
  * 계획된 익절 (수익률 > 5%)
  * 트레일링 스탑 (최고점 대비 -3%)
  * 하락시 물타기 (손실률 > -2%)
  * 급락 감지 (5분내 -5%)
  * 급등 감지 (5분내 +7%)

전략 시작:
- "매매 시작" 버튼 클릭
- 실시간 모니터링 시작
```

### **MDMS 초기 요청 패턴**
```yaml
즉시 필요한 데이터:
- KRW-BTC 15분 캔들: 60개 (RSI 계산용)
- KRW-BTC 5분 캔들: 20개 (급락/급등 감지용)
- KRW-BTC 1분 캔들: 10개 (미세 조정용)

지속적 업데이트:
- 15분마다: 새 캔들 추가, 전체 지표 재계산
- 5분마다: 급락/급등 감지 업데이트
- 1분마다: 트레일링 스탑 업데이트
```

### **스크리너와의 데이터 재사용**
```yaml
재사용 가능:
✅ KRW-BTC 1일 캔들 (이미 수집됨)
✅ 기본 ATR, RSI 계산 결과

추가 수집 필요:
❌ 15분, 5분, 1분 타임프레임 (새로 필요)
❌ 60개 기간 (스크리너는 7일만)
❌ 실시간 업데이트 스트림
```

---

## ⚡ **시나리오 2: 실시간 신호 생성 (61-120줄: 상세)**

### **실시간 모니터링 중 이벤트**
```yaml
시간: 14:45 (15분 캔들 마감 15분 전)
현재 상태: 매매 대기 중
새 1분 캔들 도착: KRW-BTC 1분 캔들 생성

MDMS 처리 플로우:
1. 새 1분 캔들 수신
2. 급락/급등 감지 계산 (5분 범위)
3. 트레일링 스탑 업데이트 (현재 가격 기준)
4. 신호 생성 여부 판단
```

### **복합 규칙 계산 요구사항**
```python
class RealTimeSignalProcessor:
    async def process_new_candle(self, symbol: str, timeframe: str, new_candle: Candle):
        """새 캔들 도착시 실시간 처리"""

        # 1. 영향받는 타임프레임 식별
        affected_timeframes = self.get_affected_timeframes(timeframe)

        # 2. 각 타임프레임별 지표 업데이트
        for tf in affected_timeframes:
            await self.update_indicators_for_timeframe(symbol, tf)

        # 3. 7규칙 상태 평가
        current_state = await self.evaluate_seven_rules(symbol)

        # 4. 신호 생성 및 액션 결정
        signal = await self.generate_trading_signal(current_state)

        return signal

    async def evaluate_seven_rules(self, symbol: str):
        """7규칙 동시 평가"""

        # 동시 계산 (의존성 고려)
        indicators = await asyncio.gather(
            self.calculate_rsi(symbol, "15m"),      # 과매도 진입
            self.calculate_profit_rate(symbol),     # 불타기/익절
            self.calculate_trailing_stop(symbol),   # 트레일링 스탑
            self.calculate_loss_rate(symbol),       # 물타기
            self.detect_flash_crash(symbol, "5m"),  # 급락 감지
            self.detect_flash_pump(symbol, "5m")    # 급등 감지
        )

        return self.combine_rule_results(indicators)
```

### **실시간 성능 요구사항**
```yaml
응답시간 목표:
- 1분 캔들 처리: 500ms 이내
- 5분 캔들 처리: 1초 이내
- 15분 캔들 처리: 2초 이내

신뢰성 요구사항:
- 캔들 누락 감지: 100%
- 계산 정확도: 99.99%
- 시스템 가용성: 99.9%

메모리 효율성:
- 심볼당 메모리: 10MB 이하
- 전체 시스템: 200MB 이하
```

---

## 🔧 **시나리오 3: 복합 상태 관리 (121-180줄: 실행)**

### **매매 상태별 다른 계산 로직**
```yaml
대기 상태 (WAITING):
- RSI 과매도 감지 (진입 신호)
- 급락 감지 (기회 포착)
- 급등 감지 (진입 취소)

진입 상태 (ENTERING):
- 체결 확인 대기
- 진입 가격 모니터링
- 취소 조건 확인

보유 상태 (HOLDING):
- 수익률 계산 (불타기/익절)
- 트레일링 스탑 추적
- 손실률 계산 (물타기)

청산 상태 (EXITING):
- 청산 체결 확인
- 최종 수익률 계산
- 다음 전략 준비
```

### **상태별 MDMS 요청 패턴**
```python
class StateBasedDataManager:
    def __init__(self):
        self.state_calculators = {
            'WAITING': WaitingStateCalculator(),
            'ENTERING': EnteringStateCalculator(),
            'HOLDING': HoldingStateCalculator(),
            'EXITING': ExitingStateCalculator()
        }

    async def process_state_change(self, old_state: str, new_state: str, symbol: str):
        """상태 변화시 계산 로직 전환"""

        # 이전 상태 계산 중단
        await self.state_calculators[old_state].stop_monitoring(symbol)

        # 새 상태 계산 시작
        await self.state_calculators[new_state].start_monitoring(symbol)

        # 상태별 데이터 요구사항 변경
        await self.adjust_data_requirements(new_state, symbol)

class HoldingStateCalculator:
    """보유 상태 전용 계산기"""

    async def start_monitoring(self, symbol: str):
        """보유 상태 모니터링 시작"""

        # 고빈도 업데이트 필요한 지표들
        self.profit_tracker = ProfitTracker(symbol)
        self.trailing_stop = TrailingStopTracker(symbol)
        self.loss_tracker = LossTracker(symbol)

        # 1분마다 업데이트
        self.monitoring_task = asyncio.create_task(
            self.continuous_monitoring(symbol)
        )

    async def continuous_monitoring(self, symbol: str):
        """지속적 모니터링"""
        while True:
            current_price = await self.get_current_price(symbol)

            # 동시 계산
            profit_signal = await self.profit_tracker.check_signal(current_price)
            trailing_signal = await self.trailing_stop.check_signal(current_price)
            loss_signal = await self.loss_tracker.check_signal(current_price)

            # 신호 우선순위 평가
            final_signal = self.evaluate_signal_priority([
                profit_signal, trailing_signal, loss_signal
            ])

            if final_signal:
                await self.emit_trading_signal(final_signal)

            await asyncio.sleep(60)  # 1분 간격
```

### **메모리 효율적 상태 관리**
```python
class EfficientStateDataManager:
    def __init__(self):
        self.state_specific_cache = {}
        self.shared_indicators = {}

    async def optimize_for_state(self, state: str, symbol: str):
        """상태별 메모리 최적화"""

        if state == 'WAITING':
            # 진입 신호만 필요, 메모리 최소화
            self.load_minimal_indicators(symbol, ['RSI', 'FLASH_DETECTION'])

        elif state == 'HOLDING':
            # 청산 신호 중심, 메모리 최대 활용
            self.load_comprehensive_indicators(symbol, [
                'PROFIT_RATE', 'TRAILING_STOP', 'LOSS_RATE'
            ])

    def share_common_calculations(self, symbols: List[str]):
        """공통 계산 결과 공유"""

        # 여러 심볼이 동일한 기준 지표 사용시
        common_market_indicators = ['MARKET_SENTIMENT', 'VOLATILITY_INDEX']

        for indicator in common_market_indicators:
            shared_result = self.calculate_once(indicator)
            for symbol in symbols:
                self.state_specific_cache[symbol][indicator] = shared_result
```

---

## 💡 **MDMS-매매변수 연동 요구사항 (181-199줄: 연결)**

### **매매 변수 계산기와의 인터페이스**
```yaml
MDMS → 매매변수계산기:
- 실시간 캔들 데이터 제공
- 계산 결과 캐싱 지원
- 의존성 해결 서비스

매매변수계산기 → MDMS:
- 필요 데이터 명세 제공
- 계산 완료 이벤트 발행
- 성능 메트릭 피드백
```

### **분산 계산 설계 필요성**
```yaml
단일 프로세스 한계:
❌ 7규칙 동시 계산시 CPU 병목
❌ 다중 심볼 처리시 메모리 부족
❌ 실시간 응답 지연 발생

분산 처리 필요:
✅ 규칙별 독립 프로세스
✅ 심볼별 워커 분리
✅ 결과 집계 및 조합
```

### **다음 설계 과제**
- **매매 변수 계산 분산 아키텍처**: 7규칙 병렬 처리
- **실시간 데이터 동기화**: MDMS-계산기 간 일관성
- **장애 복구 전략**: 개별 계산기 실패시 대응

**결론**: 매매 전략은 스크리너보다 **10배 복잡한 실시간 요구사항** 🚀
