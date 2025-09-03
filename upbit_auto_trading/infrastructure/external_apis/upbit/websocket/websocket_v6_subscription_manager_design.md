# WebSocket v6 구독 매니저 설계 문서

## 🎯 핵심 목표
**기존 realtime 스트림을 끊지 않으면서 새로운 스트림 요구사항을 효율적으로 처리**

---

## 📊 데이터 흐름

### **1단계: 컴포넌트 요청**
```
UI 컴포넌트 → SubscriptionManager.register_component(specs)
```

### **2단계: 상태 최적화**
```
_recalculate_subscriptions() → 심볼별 스트림 타입 충돌 해결
```

### **3단계: 메시지 생성**
```
WebSocketManager ← 최적화된 구독 상태 → 업비트 WebSocket 메시지
```

### **4단계: 데이터 수신**
```
업비트 응답 → WebSocketManager → 컴포넌트별 필터링 → UI 업데이트
```

---

## 🏗️ 핵심 구조

### **SubscriptionManager 책임**
- ✅ **상태 통합**: 컴포넌트별 구독 요청을 하나로 합침
- ✅ **충돌 해결**: 같은 심볼의 다른 스트림 타입 요구사항 최적화
- ❌ **메시지 생성 안함**: WebSocket 메시지는 WebSocketManager가 담당

### **WebSocketManager 책임**
- ✅ **메시지 변환**: SubscriptionManager 상태 → 업비트 API 메시지
- ✅ **전송 관리**: Rate limiting, 재전송, 연결 관리
- ✅ **응답 분배**: 수신 데이터를 컴포넌트별로 필터링

---

## 🔧 핵심 구현

### **ActiveSubscription 확장**
```python
@dataclass
class ActiveSubscription:
    data_type: DataType
    symbols: Set[str]
    components: Set[str]
    stream_type: str = "both"  # 🆕 "both", "snapshot_only", "realtime_only"
```

### **_recalculate_subscriptions() 로직**
```python
def _recalculate_subscriptions(self):
    # 1. 심볼별 스트림 요구사항 수집
    symbol_reqs = self._collect_symbol_requirements()

    # 2. 충돌 해결 (기존 realtime 보호)
    optimized = self._resolve_stream_conflicts(symbol_reqs)

    # 3. 스트림 타입별 그룹화
    self._create_optimized_subscriptions(optimized)
```

### **충돌 해결 규칙**
```python
def _resolve_stream_conflicts(self, reqs):
    for symbol, type_reqs in reqs.items():
        if "realtime_only" in type_reqs and "snapshot_only" in type_reqs:
            # realtime + snapshot 요구 → "both"로 업그레이드
            return "both"
        elif len(type_reqs) == 1:
            # 단일 요구사항 → 그대로 사용
            return list(type_reqs)[0]
```

---

## 🎯 시나리오별 동작

### **시나리오 1: 기본 구독**
```
컴포넌트A: ticker[KRW-BTC] (기본값)
→ ActiveSubscription(stream_type="both")
→ WebSocket: {"type": "ticker", "codes": ["KRW-BTC"]}
```

### **시나리오 2: 스트림 충돌**
```
컴포넌트A: ticker[KRW-BTC] (realtime만)  ← 이미 활성
컴포넌트B: ticker[KRW-BTC] (snapshot만) ← 새 요청

충돌 해결:
→ ActiveSubscription(stream_type="both")  ← 업그레이드
→ WebSocket: {"type": "ticker", "codes": ["KRW-BTC"]}

클라이언트 필터링:
- 컴포넌트A: stream_type=="REALTIME"만 사용
- 컴포넌트B: stream_type=="SNAPSHOT"만 사용
```

### **시나리오 3: 복잡한 충돌**
```
컴포넌트A: ticker[KRW-BTC, KRW-ETH] (realtime만)
컴포넌트B: ticker[KRW-BTC] (snapshot만)

최적화 결과:
→ ActiveSubscription(data_type=ticker, symbols=[KRW-BTC], stream_type="both")
→ ActiveSubscription(data_type=ticker, symbols=[KRW-ETH], stream_type="realtime_only")

WebSocket 메시지:
[
  {"type": "ticker", "codes": ["KRW-BTC"]},
  {"type": "ticker", "codes": ["KRW-ETH"], "isOnlyRealtime": true}
]
```

---

## 🚨 설계 우려사항

### **❌ 복잡성 증가**
- 현재 단순한 구조를 복잡하게 만들 위험
- 스트림 타입별로 ActiveSubscription을 나누면 관리 포인트 증가

### **❌ 성능 오버헤드**
- 매번 충돌 분석 + 최적화 계산
- 기존 단순 합집합 방식 대비 연산 복잡도 증가

### **❌ 기존 코드 호환성**
- `get_public_subscriptions()` 등 기존 API 변경 필요
- WebSocketManager와의 인터페이스 재설계 필요

---

## 💡 간단한 대안

### **Option A: 현재 구조 유지 + 클라이언트 필터링**
```python
# SubscriptionManager: 기존 단순 통합 유지
ActiveSubscription(symbols={KRW-BTC, KRW-ETH})

# WebSocketManager: 항상 기본값 전송
{"type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"]}

# 클라이언트: 필요한 stream_type만 사용
component_a.filter(lambda msg: msg.stream_type == "REALTIME")
component_b.filter(lambda msg: msg.stream_type == "SNAPSHOT")
```

### **Option B: 최소 변경 + 스마트 업그레이드**
```python
# SubscriptionManager: 기존 구조 + stream_type 필드만 추가
def _recalculate_subscriptions(self):
    # 기존 로직 유지하되, stream_type만 계산
    for data_type, active_sub in subscriptions.items():
        active_sub.stream_type = self._determine_optimal_stream_type(active_sub)
```

---

## 🎯 권장사항

**현 시점에서는 Option A (클라이언트 필터링) 권장**

### **이유**:
1. **최소 변경**: 기존 코드 99% 유지
2. **단순함**: 복잡한 충돌 해결 로직 불필요
3. **안정성**: 검증된 구조 기반
4. **성능**: 오버헤드 최소화

### **구현**:
1. **SubscriptionManager**: 현재 구조 유지
2. **WebSocketManager**: 기본값 메시지 전송
3. **WebSocketClient**: 컴포넌트별 stream_type 필터링 추가

이 방식이 **가장 실용적이고 안전한 접근**입니다! 🚀
