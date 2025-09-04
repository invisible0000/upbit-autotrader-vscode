# 🚀 WebSocket v6 클라이언트 사용 가이드

## 📖 **개념적 설명**

### **1. 복합 구독 vs 단일 구독**

#### **✅ 복합 구독 (권장)**
동일한 클라이언트에서 여러 데이터 타입을 동시에 구독할 수 있습니다.

```python
# 하나의 클라이언트로 여러 데이터 타입 구독
client = WebSocketClient("multi_data_client")

# ticker 구독
await client.subscribe_ticker(['KRW-BTC'], ticker_callback)

# orderbook 구독 추가 (ticker 유지)
await client.subscribe_orderbook(['KRW-BTC'], orderbook_callback)

# trade 구독 추가 (ticker + orderbook 유지)
await client.subscribe_trade(['KRW-BTC'], trade_callback)

# 결과: ticker, orderbook, trade 모두 동시 수신 ✅
```

#### **🔄 단일 구독 (개별 관리)**
각 데이터 타입별로 별도 클라이언트를 생성합니다.

```python
# 각 기능별로 독립적인 클라이언트
ticker_client = WebSocketClient("ticker_only")
await ticker_client.subscribe_ticker(['KRW-BTC'], ticker_callback)

orderbook_client = WebSocketClient("orderbook_only")
await orderbook_client.subscribe_orderbook(['KRW-BTC'], orderbook_callback)

# 개별 해제 가능
await ticker_client.cleanup()  # ticker만 해제
# orderbook_client는 계속 동작
```

### **2. 하위 매니저 직접 호출**

#### **개념**
WebSocketClient 내부의 구독 관리자에 직접 접근하여 세밀한 제어를 수행합니다.

#### **사용 예시**
```python
client = WebSocketClient("advanced_client")
await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH'], ticker_callback)

# 하위 매니저 직접 접근으로 특정 심볼만 해제
if client._manager and hasattr(client._manager, 'subscription_manager'):
    manager = client._manager.subscription_manager

    # KRW-ETH만 구독 해제 (KRW-BTC는 유지)
    await manager.unsubscribe_symbols(
        symbols=['KRW-ETH'],
        subscription_type=SubscriptionType.TICKER
    )
```

#### **⚠️ 주의사항**
- 고급 사용법으로 내부 구조 변경에 영향받을 수 있음
- 일반 사용에는 권장하지 않음
- 디버깅이나 특수한 경우에만 사용

---

## 📋 **사용 패턴 비교**

| 방식 | 장점 | 단점 | 권장 상황 |
|------|------|------|-----------|
| **복합 구독** | 단일 연결, 효율적 리소스 사용 | 전체 해제만 가능 | 관련 데이터를 함께 사용하는 경우 |
| **단일 구독** | 개별 해제 가능, 명확한 분리 | 다수 연결, 리소스 오버헤드 | 독립적 기능, 개별 제어 필요 |
| **하위 직접 호출** | 세밀한 제어 가능 | 복잡성 증가, 안정성 위험 | 고급 최적화, 특수 요구사항 |

---

## 🎯 **권장 사용법**

### **시나리오 1: 차트 애플리케이션**
```python
# 차트용 복합 구독 (권장)
chart_client = WebSocketClient("chart_viewer")
await chart_client.subscribe_ticker(['KRW-BTC'], on_price_update)
await chart_client.subscribe_orderbook(['KRW-BTC'], on_orderbook_update)
await chart_client.subscribe_trade(['KRW-BTC'], on_trade_update)
```

### **시나리오 2: 모듈별 분리**
```python
# 각 모듈별 독립 클라이언트 (권장)
price_monitor = WebSocketClient("price_monitor")
await price_monitor.subscribe_ticker(['KRW-BTC', 'KRW-ETH'], on_price_alert)

trading_engine = WebSocketClient("trading_engine")
await trading_engine.subscribe_trade(['KRW-BTC'], on_trading_signal)

# 독립적 종료 가능
await price_monitor.cleanup()  # 가격 모니터링만 중지
```

### **시나리오 3: 고급 제어 (신중히 사용)**
```python
client = WebSocketClient("advanced_control")
await client.subscribe_ticker(['KRW-BTC', 'KRW-ETH', 'KRW-XRP'], callback)

# 특정 심볼만 해제하고 싶은 경우
if hasattr(client, '_manager') and client._manager:
    subscription_manager = client._manager.subscription_manager
    await subscription_manager.unsubscribe_symbols(
        symbols=['KRW-XRP'],
        subscription_type=SubscriptionType.TICKER
    )
```

---

## ⚡ **성능 고려사항**

### **cleanup() 성능 문제**
- 현재 cleanup()은 약 1초 소요 (측정값: 1.004~1.009s)
- 여러 레이어를 거치는 복잡한 해제 과정이 원인
- 빈번한 cleanup() 호출 시 성능 영향 고려 필요

### **개선 방안**
1. **빈 구독 덮어쓰기 방식** 사용 (99.3% 성능 향상)
2. **연결 재사용** 최대화
3. **불필요한 cleanup() 호출 최소화**
