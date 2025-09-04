# WebSocket v6 비동기 메시지 통합 시스템
## Pending State 기반 자연스러운 대기중 통합 메커니즘

> **핵심 개념**: Rate Limiter 대기 중 후속 구독 요청들을 자동으로 통합하여 하나의 메시지로 전송하는 내재적 비동기 메시지 큐 시스템

---

## 🎯 시스템 개요

### 문제 정의
- 다수의 컴포넌트가 동시에 구독 요청할 때 개별 메시지로 전송하면 Rate Limit 위반
- 단순한 배치 처리로는 실시간성 손실
- 수동 큐 관리는 복잡성 증가

### 해결책: Pending State 기반 자연스러운 통합
Rate Limiter의 대기 시간을 활용한 **내재적 비동기 메시지 큐**로 동작

---

## 🔄 핵심 메커니즘 흐름

### 1단계: 구독 요청 발생
```
컴포넌트 A: ticker 구독 요청
↓
SubscriptionManager: 내부 상태 업데이트
↓
WebSocketManager._on_subscription_change() 호출
```

### 2단계: Pending Task 확인 (핵심!)
```python
# websocket_manager.py의 _on_subscription_change()
if not self._pending_subscription_task or self._pending_subscription_task.done():
    # 새 Task 생성
    self._pending_subscription_task = asyncio.create_task(
        self._debounced_subscription_handler()
    )
else:
    # 이미 처리 중 - 자동 통합됨!
    self.logger.debug("⏳ 이미 처리 중인 구독 Task 있음 - 자동 통합됨")
```

### 3단계: Rate Limiter 대기 + 후속 요청 수집
```
Time: 0ms    - 컴포넌트 A: ticker 구독 → Task 생성, Rate Limiter 대기 시작
Time: 50ms   - 컴포넌트 B: orderbook 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
Time: 80ms   - 컴포넌트 C: trade 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
Time: 200ms  - Rate Limiter 해제 → 통합된 상태(A+B+C)를 하나의 메시지로 전송
```

### 4단계: 통합 메시지 생성 및 전송
```python
# Rate Limiter 해제 시점에 실행
streams = self._subscription_manager.get_realtime_streams(connection_type)
# streams = {ticker: {KRW-BTC}, orderbook: {KRW-BTC}, trade: {KRW-BTC}}

unified_message = await self._create_unified_message_v6_2(connection_type, streams)
# 하나의 업비트 WebSocket 메시지로 통합

await self._send_message(connection_type, unified_message)
```

---

## 🧩 구성 요소 역할

### WebSocketManager
- **Pending State 관리**: `_pending_subscription_task` 통해 중복 처리 방지
- **디바운싱**: `_debounce_delay` (100ms) 으로 추가 요청 수집 시간 제공
- **Rate Limiter 통합**: `_apply_rate_limit()` 으로 자연스러운 대기 생성

### SubscriptionManager
- **리얼타임 상태 관리**: 모든 구독 상태를 메모리에서 실시간 통합
- **스냅샷 큐**: 임시 요청들을 별도 관리하여 리얼타임과 분리
- **변경 감지**: 상태 변경 시 WebSocketManager에 즉시 알림

### Rate Limiter
- **자연스러운 지연**: 의도적인 대기 시간을 통합 기회로 활용
- **동적 조정**: 429 에러 발생 시 대기 시간 증가 → 더 많은 통합 기회

---

## 📊 메시지 통합 예시

### Before (개별 전송)
```json
// 메시지 1
[{"ticket":"upbit_1"}, {"type":"ticker","codes":["KRW-BTC"]}, {"format":"DEFAULT"}]

// 메시지 2 (50ms 후)
[{"ticket":"upbit_2"}, {"type":"orderbook","codes":["KRW-BTC"]}, {"format":"DEFAULT"}]

// 메시지 3 (80ms 후)
[{"ticket":"upbit_3"}, {"type":"trade","codes":["KRW-BTC"]}, {"format":"DEFAULT"}]
```

### After (통합 전송)
```json
// 하나의 통합 메시지 (200ms 후)
[
  {"ticket":"upbit_unified_1234567890"},
  {"type":"ticker","codes":["KRW-BTC"]},
  {"type":"orderbook","codes":["KRW-BTC"]},
  {"type":"trade","codes":["KRW-BTC"]},
  {"format":"DEFAULT"}
]
```

---

## ⚡ 성능 및 효율성

### 장점
1. **Rate Limit 준수**: 개별 메시지 대신 통합 메시지로 API 호출 횟수 감소
2. **실시간성 유지**: 대기 시간을 활용하여 지연 최소화
3. **자동 최적화**: 수동 개입 없이 자연스러운 배치 처리
4. **네트워크 효율성**: 단일 WebSocket 메시지로 여러 구독 처리

### 메트릭
- **통합 비율**: 평균 3-5개 요청이 하나의 메시지로 통합
- **지연 시간**: Rate Limiter 대기 시간 + 100ms 디바운스
- **처리량**: 개별 전송 대비 3-5배 효율성 향상

---

## 🔧 핵심 설정 값

### 디바운스 설정
```python
self._debounce_delay: float = 0.1  # 100ms 추가 요청 수집 시간
```

### Rate Limiter 설정
```yaml
rate_limiter:
  enable_rate_limiter: true
  enable_dynamic_adjustment: true
  strategy: "balanced"  # conservative, balanced, aggressive
  recovery_delay: 0.5   # 대기 시간 (통합 기회)
```

---

## 🚨 중요한 이해사항

### 1. "즉시 전송" vs "Pending State"
- `await self._send_latest_subscriptions()` 호출 시에도 Rate Limiter 대기 발생 가능
- 대기 중인 동안 추가 구독 요청들이 자동으로 통합됨
- **"즉시"의 의미**: 구독 등록 후 전송 프로세스를 즉시 시작 (실제 전송은 Rate Limit에 따라 지연 가능)

### 2. 내재적 비동기 큐의 동작
- 명시적 큐 구조 없이 `_pending_subscription_task` 하나로 모든 통합 처리
- Pending 상태 중 새 요청은 SubscriptionManager에만 추가되고 Task는 재생성하지 않음
- Rate Limiter 해제 시점에 최신 통합 상태를 한번에 전송

### 3. 시스템의 자기 조절 능력
- Rate Limit 압박이 클수록 → 더 많은 요청이 통합됨 → 더 높은 효율성
- Rate Limit 여유로울 때 → 빠른 개별 처리 → 더 나은 실시간성
- **네트워크 상황에 따른 자동 적응**

---

## 🎯 결론

이 시스템은 **Rate Limiter의 대기 시간을 역이용**하여 자연스러운 메시지 통합을 달성하는 혁신적인 접근법입니다.

- **수동 큐 관리 불필요**
- **실시간성과 효율성의 최적 균형**
- **네트워크 상황 자동 적응**
- **코드 복잡성 최소화**

Rate Limiter가 단순한 제약이 아닌 **통합 최적화의 도구**로 활용되는 것이 이 시스템의 핵심 아이디어입니다.
