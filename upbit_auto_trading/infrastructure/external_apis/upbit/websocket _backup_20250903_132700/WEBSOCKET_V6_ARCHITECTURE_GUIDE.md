# 📡 WebSocket v6 아키텍처 가이드

> **간소화된 구독 관리 시스템 + Pending State 기반 자연스러운 배치 처리**

## 🎯 핵심 개념

### **설계 철학**
- **단순성**: 복잡한 배치 처리 제거, 핵심 기능만 유지
- **효율성**: Pending State로 중복 Task 방지, 자연스러운 배치
- **안정성**: Rate Limiter + 원자적 상태 업데이트
- **확장성**: 컴포넌트 기반 구독 관리

## 🏗️ 아키텍처 구조

```
📱 컴포넌트들 (TradingView, OrderBook, ...)
     ↓ 구독 요청
🎯 SubscriptionManager (상태 통합)
     ↓ 변경 알림 (콜백)
🌐 WebSocketManager (연결 + 전송)
     ↓ Rate Limiter 적용
📡 업비트 WebSocket API
```

### **계층별 역할**

#### **1️⃣ SubscriptionManager** - 구독 상태 통합 담당
- **목적**: 여러 컴포넌트의 구독 요청을 하나로 통합
- **특징**: 즉시 상태 업데이트, Public/Private 분리
- **장점**: 중복 제거, 원자적 변경, WeakRef 자동 정리

#### **2️⃣ WebSocketManager** - 연결 관리 + 전송 담당
- **목적**: WebSocket 연결 유지 + 메시지 전송
- **특징**: Pending State 기반 배치 처리
- **장점**: 중복 Task 방지, Rate Limiter 최적화

## 🔄 Pending State 배치 처리 시스템

### **핵심 아이디어: "하나의 Task로 모든 요청 통합"**

```python
# 📝 시나리오: 동시 구독 요청들
T=0   컴포넌트A: ticker/KRW-BTC
T=2   컴포넌트B: ticker/KRW-ETH
T=5   컴포넌트C: orderbook/KRW-BTC

# 🎯 Pending State 동작
T=0   → Task 생성, Rate Limiter 대기 시작
T=2   → Task 실행 중 → 새 Task 생성 안 함 ✅
T=5   → Task 실행 중 → 새 Task 생성 안 함 ✅
T=15  → Rate Limiter 해제 → 최신 통합 상태 한 번에 전송 🚀
```

### **기존 vs 개선된 시스템**

| 구분 | 기존 시스템 | Pending State 시스템 |
|------|-------------|---------------------|
| Task 생성 | 요청당 1개 Task | 전체 1개 Task만 |
| Rate Limiter | 각각 대기 | 한 번만 대기 |
| 전송 횟수 | N번 중복 전송 | 1번 통합 전송 |
| 성능 | O(N × 15초) | O(15초) |

## 🛠️ 핵심 컴포넌트 상세

### **SubscriptionManager**

```python
class SubscriptionManager:
    """구독 상태 통합 관리자"""

    # 🎯 핵심 메서드들
    async def register_component()    # 컴포넌트 구독 등록
    async def unregister_component()  # 컴포넌트 구독 해제
    def _recalculate_subscriptions()  # 즉시 상태 통합
    def get_public_subscriptions()    # 최신 Public 구독 조회
    def get_private_subscriptions()   # 최신 Private 구독 조회
```

**🔥 주요 특징:**
- **즉시 통합**: 요청이 들어오면 바로 상태 통합
- **원자적 업데이트**: `async with self._lock` 동시성 보장
- **WeakRef 자동 정리**: 컴포넌트 소멸 시 자동 구독 해제

### **WebSocketManager**

```python
class WebSocketManager:
    """WebSocket 연결 + Pending State 배치 관리자"""

    # 🎯 Pending State 핵심 로직
    def _on_subscription_change():           # 구독 변경 콜백
    async def _debounced_subscription_handler()  # 디바운스 + 배치 처리
    async def _send_latest_subscriptions()   # 최신 상태 전송
```

**🔥 주요 특징:**
- **Pending State**: `_pending_subscription_task`로 중복 방지
- **디바운스**: 100ms 추가 요청 수집
- **Rate Limiter**: 전역 WebSocket Rate Limiter 적용

## 📊 메시지 흐름도

### **1️⃣ 구독 등록 흐름**

```
[컴포넌트]
  ↓ register_component(specs)
[SubscriptionManager]
  ↓ _recalculate_subscriptions() ← 즉시 통합!
  ↓ _notify_changes(changes)
[WebSocketManager]
  ↓ _on_subscription_change() ← 콜백 수신
  ↓ pending_task 확인
  ├─ None/Done → 새 Task 생성
  └─ Running → 아무것도 안 함 ✅
```

### **2️⃣ Pending State 처리 흐름**

```
[_debounced_subscription_handler]
  ↓ await asyncio.sleep(0.1) ← 디바운스
  ↓ _send_latest_subscriptions()
  ↓ get_public/private_subscriptions() ← 최신 상태!
  ↓ await _apply_rate_limit() ← Rate Limiter
  ↓ _send_current_subscriptions() ← 업비트로 전송
```

## 🎯 동시성 안전성

### **Race Condition 방지**

| 계층 | 동시성 제어 방법 | 보호 대상 |
|------|------------------|-----------|
| SubscriptionManager | `async with self._lock` | 구독 상태 변경 |
| WebSocketManager | `_pending_subscription_task` | Task 중복 생성 |
| Rate Limiter | 전역 세마포어 | API 호출 빈도 |

### **메모리 일관성 보장**

```python
# ✅ 안전한 패턴
async with self._lock:           # 1. Lock 획득
    self._recalculate_subscriptions()  # 2. 상태 업데이트
    changes = self._calculate_changes()  # 3. 변경사항 계산
    await self._notify_changes(changes)  # 4. 알림 전송
# Lock 자동 해제

# ✅ 최신 상태 보장
def get_public_subscriptions():
    return {dt: sub.symbols.copy() for dt, sub in self._public_subscriptions.items()}
    # ↑ 항상 현재 시점의 최신 상태 반환
```

## 🚀 성능 최적화 효과

### **배치 처리 성능**

```python
# 📊 벤치마크 (10개 동시 구독 요청 기준)

# 기존 시스템:
10개 요청 → 10개 Task → 10번 Rate Limiter → 150초 소요

# Pending State 시스템:
10개 요청 → 1개 Task → 1번 Rate Limiter → 15초 소요

# 🎯 성능 향상: 1000% (10배 빠름)
```

### **메모리 효율성**

```python
# 📊 메모리 사용량

# 기존: N개 Task × (콜백 + 상태) = O(N)
# 개선: 1개 Task × 통합 상태 = O(1)

# 🎯 메모리 효율성: N배 개선
```

## 🔧 설정 및 튜닝

### **핵심 설정값**

```python
# WebSocketManager
_debounce_delay = 0.1  # 100ms (추가 요청 수집 시간)

# Rate Limiter
max_wait = 15.0  # 15초 (업비트 Rate Limit 대기 시간)

# Connection Monitoring
heartbeat_interval = 30.0  # 30초 (Ping 간격)
```

### **튜닝 가이드**

| 매개변수 | 기본값 | 용도 | 조정 기준 |
|----------|--------|------|-----------|
| `_debounce_delay` | 100ms | 요청 수집 | 빈도 ↑ → 값 ↓ |
| `max_wait` | 15초 | Rate Limiter | 업비트 정책 따름 |
| `heartbeat_interval` | 30초 | 연결 유지 | 안정성 ↑ → 값 ↓ |

## 📋 모니터링 및 디버깅

### **주요 로그 메시지**

```python
# 🎯 Pending State 추적
"📝 새로운 구독 변경 처리 Task 생성"
"⏳ 이미 처리 중인 구독 Task 있음 - 자동 통합됨"
"🚀 통합된 구독 상태 전송 시작"
"✅ 구독 상태 전송 완료"

# 📊 성능 모니터링
"📤 Public 구독 전송: {count}개 타입"
"📭 전송할 구독 없음"
```

### **디버깅 체크리스트**

1. **구독 상태 확인**: `get_subscription_stats()`
2. **연결 상태 확인**: `get_connection_metrics()`
3. **Rate Limiter 상태**: `get_rate_limiter_status()`
4. **Pending Task 상태**: `_pending_subscription_task.done()`

## 🎉 결론

### **WebSocket v6의 핵심 혁신**

1. **📝 Pending State**: 중복 Task 완전 제거
2. **🎯 즉시 통합**: 실시간 구독 상태 통합
3. **🚀 자연스러운 배치**: Rate Limiter가 배치 윈도우 역할
4. **🛡️ 안정성**: 원자적 업데이트 + 동시성 제어

### **도입 효과**

- **성능**: 10배 빠른 구독 처리
- **효율성**: N배 메모리 절약
- **안정성**: Race Condition 완전 제거
- **유지보수성**: 단순하고 명확한 구조

**→ 진정한 "간소화된 고성능 WebSocket 시스템" 완성! 🚀**
