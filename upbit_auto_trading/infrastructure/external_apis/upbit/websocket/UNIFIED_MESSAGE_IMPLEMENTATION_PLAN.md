# 웹소켓 통합 메시지 구현 계획 (v6.1)

## 🎯 목표
- **리얼타임/기본값 요청 분리**: 원론적인 리얼타임 요청과 기본값(스냅샷+리얼타임) 분리
- **통합 메시지 생성**: 모든 데이터 타입을 하나의 메시지로 통합 전송
- **Rate Limiter 펜딩 통합**: 제한 시 추가 요청들을 자동 통합, 해제 즉시 전송
- **클라이언트 필터링**: 컴포넌트별 필요한 stream_type만 수신

---

## 📋 구현 단계

### **1단계: 클라이언트 필터링 시스템** ⚡ (30분)
**현재 상태**: ❌ 미구현
**구현 필요**: ComponentSubscription에 stream_filter 추가

```python
@dataclass
class ComponentSubscription:
    component_id: str
    subscriptions: List[SubscriptionSpec]
    callback: Optional[Callable]
    stream_filter: Optional[str] = None  # 🆕 "SNAPSHOT", "REALTIME", None
```

### **2단계: 통합 메시지 생성 시스템** 🚀 (45분)
**현재 상태**: ❌ 미구현 (개별 타입별 메시지만 가능)
**구현 필요**: `_create_unified_message()` 메서드 추가

```python
def _create_unified_message(self, ws_type: WebSocketType, subscriptions: Dict) -> str:
    """모든 데이터 타입을 하나의 메시지로 통합"""
    message_parts = [{"ticket": f"upbit_websocket_v6_{int(time.time())}"}]

    # 🎯 모든 데이터 타입을 하나의 메시지에 포함
    for data_type, symbols in subscriptions.items():
        if symbols:
            message_parts.append({
                "type": data_type.value,
                "codes": list(symbols)
            })

    message_parts.append({"format": "DEFAULT"})
    return json.dumps(message_parts)
```

### **3단계: Rate Limiter 펜딩 통합** 🔄 (30분)
**현재 상태**: ✅ 부분 구현됨 (`_pending_subscription_task` 존재)
**개선 필요**: `_send_latest_subscriptions()` 통합 메시지 사용

```python
async def _send_latest_subscriptions(self) -> None:
    """Rate Limiter 해제 시 통합 메시지 전송"""
    # Public 통합 메시지
    public_subs = self._subscription_manager.get_public_subscriptions()
    if public_subs:
        unified_message = self._create_unified_message(WebSocketType.PUBLIC, public_subs)
        await self._apply_rate_limit()
        await self._send_message(WebSocketType.PUBLIC, unified_message)

    # Private 통합 메시지
    private_subs = self._subscription_manager.get_private_subscriptions()
    if private_subs:
        unified_message = self._create_unified_message(WebSocketType.PRIVATE, private_subs)
        await self._apply_rate_limit()
        await self._send_message(WebSocketType.PRIVATE, unified_message)
```

---

## ✅ 통합 메시지 형태

### **Public 통합 메시지** (ticker + orderbook + trade)
```json
[
  {"ticket": "upbit_websocket_v6_1725350400"},
  {
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "KRW-ADA"]
  },
  {
    "type": "orderbook",
    "codes": ["KRW-BTC"]
  },
  {
    "type": "trade",
    "codes": ["KRW-BTC", "KRW-ETH"]
  },
  {"format": "DEFAULT"}
]
```

### **Private 통합 메시지** (myOrder + myAsset)
```json
[
  {"ticket": "upbit_websocket_v6_1725350401"},
  {
    "type": "myOrder"
  },
  {
    "type": "myAsset"
  },
  {"format": "DEFAULT"}
]
```

---

## 📊 현재 시스템 지원 현황

### ✅ **이미 구현됨**
1. **Public/Private 분리**: 별도 웹소켓 연결 관리
2. **Rate Limiter 통합**: `_pending_subscription_task` 기반 디바운스
3. **구독 상태 통합**: SubscriptionManager에서 컴포넌트별 요청 통합
4. **기본 메시지 생성**: 개별 데이터 타입별 메시지 생성

### ❌ **구현 필요**
1. **통합 메시지 생성**: 모든 타입을 하나의 메시지로 생성
2. **클라이언트 필터링**: stream_type별 선택적 수신
3. **스트림 타입 분리**: realtime_only, snapshot_only 옵션

---

## 🎯 핵심 동작 원리

### **Rate Limiter 펜딩 시나리오**
1. **요청 A**: ticker 구독 → Rate Limiter 대기 (펜딩 Task 생성)
2. **요청 B**: orderbook 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
3. **요청 C**: trade 구독 → 기존 Task 있음, SubscriptionManager만 업데이트
4. **Rate Limiter 해제** → 최신 통합 상태(A+B+C)를 **하나의 통합 메시지**로 전송

### **즉시 전송 원리**
- **펜딩 Task 없음** + **Rate Limiter 통과** = 즉시 통합 메시지 전송
- **펜딩 Task 있음** = 자동 통합, 나중에 한 번에 전송

---

## 📅 구현 일정

| 단계 | 작업 | 소요시간 | 상태 |
|------|------|----------|------|
| 1단계 | 클라이언트 필터링 | 30분 | ❌ 대기 |
| 2단계 | 통합 메시지 생성 | 45분 | ❌ 대기 |
| 3단계 | Rate Limiter 개선 | 30분 | ❌ 대기 |

**총 예상 시간: 1시간 45분** 🚀

---

## 🎯 검증 방법

```python
# 테스트 시나리오: 동시 다중 구독
component_a = register_component("chart", [ticker_spec, orderbook_spec])
component_b = register_component("algo", [trade_spec])

# 예상 결과: 하나의 통합 메시지
# [{"ticket": "..."}, {"type": "ticker", "codes": [...]},
#  {"type": "orderbook", "codes": [...]}, {"type": "trade", "codes": [...]},
#  {"format": "DEFAULT"}]
```

이 계획으로 **효율적인 통합 메시지 시스템**을 구축할 수 있습니다! 🎯
