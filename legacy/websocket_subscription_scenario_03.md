# 웹소켓 구독 시나리오 03: v6.2 고급 조합 테스트

## 개요
SubscriptionManager v6.2의 복잡한 상황 처리 능력을 3초 내로 빠르게 검증하는 고급 시나리오

---

## 시나리오 1: 복잡한 구독 충돌 해결

### 상황
같은 심볼(KRW-BTC)에 3개 컴포넌트가 서로 다른 스트림 타입 요구

### 테스트 시퀀스
```python
# 1단계: 충돌하는 컴포넌트들 등록
component_a = MockComponent("algo_trader", [
    SubscriptionSpec(DataType.TICKER, ["KRW-BTC"])
])

component_b = MockComponent("price_checker", [
    SubscriptionSpec(DataType.TICKER, ["KRW-BTC"])
])

component_c = MockComponent("chart_display", [
    SubscriptionSpec(DataType.ORDERBOOK, ["KRW-BTC"])
])

# 2단계: 충돌 해결 확인
# 결과: ticker + orderbook 스트림 생성
# 검증: 3개 컴포넌트 → 2개 스트림 타입으로 통합

# 3단계: 순차 해제
# unregister_component("price_checker")
# unregister_component("chart_display")
# 결과: 마지막 컴포넌트만 남아서 ticker만 유지
```

### 검증 포인트
- ✅ 3개 컴포넌트 → ticker + orderbook 스트림 생성
- ✅ 순차 해제 시 스트림 정확한 정리

---

## 시나리오 2: 다중 데이터 타입 조합

### 상황
ticker + orderbook + trade 복합 구독 테스트

### 테스트 시퀀스
```python
# 1단계: 복합 구독 컴포넌트 등록
complex_component = MockComponent("trading_dashboard", [
    SubscriptionSpec(DataType.TICKER, ["KRW-BTC", "KRW-ETH"]),
    SubscriptionSpec(DataType.ORDERBOOK, ["KRW-BTC"]),
    SubscriptionSpec(DataType.TRADE, ["KRW-BTC", "KRW-ETH"])
])

# 2단계: 부분 심볼 추가
additional_component = MockComponent("additional_monitor", [
    SubscriptionSpec(DataType.TICKER, ["KRW-XRP", "KRW-ADA"])
])

# 결과: 4개 심볼(BTC, ETH, XRP, ADA) ticker 통합 관리
```

### 검증 포인트
- ✅ 다중 데이터 타입 정확한 조합
- ✅ 심볼 추가 시 기존 스트림과 통합

---

## 시나리오 3: 동적 컴포넌트 관리

### 상황
컴포넌트들이 동적으로 등록/해제될 때 리얼타임 스트림 상태 정확성 검증

### 테스트 시퀀스
```python
# 1단계: 다중 컴포넌트 동시 등록
components = [
    ("chart_btc", [SubscriptionSpec(DataType.TICKER, ["KRW-BTC"])]),
    ("chart_eth", [SubscriptionSpec(DataType.TICKER, ["KRW-ETH"])]),
    ("orderbook_btc", [SubscriptionSpec(DataType.ORDERBOOK, ["KRW-BTC"])]),
    ("trade_analyzer", [SubscriptionSpec(DataType.TRADE, ["KRW-BTC", "KRW-ETH"])])
]

# 2단계: 선택적 해제
# unregister_component("chart_eth")     # ETH 차트 해제
# unregister_component("trade_analyzer") # Trade 분석기 해제

# 결과: BTC ticker + orderbook만 남음
```

### 검증 포인트
- ✅ 컴포넌트 해제 시 스트림 정확히 정리
- ✅ 동적 관리 시 상태 일관성 유지

---

## 시나리오 4: 구독 최적화

### 상황
중복 구독 및 불필요한 구독이 최적화되는지 검증

### 테스트 시퀀스
```python
# 1단계: 중복 구독 생성
duplicate_components = [
    MockComponent(f"component_{i}", [
        SubscriptionSpec(DataType.TICKER, ["KRW-BTC"])
    ]) for i in range(3)
]

# 결과: 3개 컴포넌트 → 1개 스트림으로 통합

# 2단계: 순차 해제로 최적화 지속성 확인
# unregister_component("component_0")
# unregister_component("component_1")
# 결과: 마지막 컴포넌트까지 스트림 유지
```

### 검증 포인트
- ✅ 3개 중복 구독 → 1개 통합 스트림
- ✅ 최적화 지속성 (마지막까지 스트림 유지)

---

## Mock 이벤트 시뮬레이션

### 핵심 특징
```python
class MockWebSocketEventGenerator:
    """실제 WebSocket 연결 없이 이벤트 모사"""

    async def generate_mock_events(self, duration: float, subscriptions: Dict):
        # 구독 상태에 맞는 Mock 이벤트 생성
        # ticker: {'type': 'ticker', 'code': 'KRW-BTC', 'trade_price': 154428000.0}
        # orderbook: {'type': 'orderbook', 'code': 'KRW-BTC', 'orderbook_units': [...]}
        # trade: {'type': 'trade', 'code': 'KRW-BTC', 'trade_price': 154428000.0}
```

### 테스트 환경
- **실행 시간**: 각 시나리오 3초 내 완료
- **연결 방식**: 실제 WebSocket 연결 없이 Mock 시뮬레이션
- **검증 방법**: SubscriptionManager v6.2 상태 변화 추적

---

## 실행 결과 예시

```
🔧 WebSocket v6.2 고급 시나리오 테스트 시작
============================================================
📋 테스트 계획:
   - 시나리오 1: 복잡한 구독 충돌 해결 (3초)
   - 시나리오 2: 다중 데이터 타입 조합 (3초)
   - 시나리오 3: 동적 컴포넌트 관리 (3초)
   - 시나리오 4: 구독 최적화 (3초)
============================================================

🧪 시나리오 1: 복잡한 구독 충돌 해결
   ✅ 3개 컴포넌트 → ticker + orderbook 스트림 생성
   🎉 복잡한 구독 관리 성공!

🧪 시나리오 2: 다중 데이터 타입 조합
   ✅ 4개 심볼 ticker 통합 관리
   🎉 다중 데이터 타입 조합 성공!

🧪 시나리오 3: 동적 컴포넌트 관리
   ✅ 컴포넌트 해제 시 스트림 정확히 정리됨
   🎉 동적 컴포넌트 관리 성공!

🧪 시나리오 4: 구독 최적화
   ✅ 3개 중복 구독 → 1개 통합 스트림
   🎉 구독 최적화 성공!

🏁 고급 시나리오 테스트 완료: 12.5초

🎯 v6.2 고급 기능 검증:
   ✅ 복잡한 구독 충돌이 효율적으로 해결되는가?
   ✅ 다중 데이터 타입이 올바르게 조합되는가?
   ✅ 컴포넌트 동적 관리가 정확히 동작하는가?
   ✅ 중복 구독이 최적화되어 통합되는가?

💡 이 결과로 SubscriptionManager v6.2의 고급 기능 완전 검증!
```

---

## 핵심 가치

### 🚀 **빠른 검증**
- 실제 WebSocket 연결 없이 3초 내 완료
- Mock 이벤트 시뮬레이션으로 안전한 테스트

### 🎯 **고급 기능 커버리지**
- 구독 충돌 해결
- 다중 데이터 타입 조합
- 동적 컴포넌트 관리
- 구독 최적화

### 💡 **실용적 접근**
- 실제 업무에서 발생하는 복잡한 시나리오
- SubscriptionManager v6.2의 핵심 기능 검증
