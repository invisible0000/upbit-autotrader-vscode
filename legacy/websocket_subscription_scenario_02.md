# 웹소켓 구독 시나리오 02: 멀티탭 & 프라이빗 연동

## 개요
차트뷰, 거래내역, 잔고, 주문 탭이 동시에 열린 복합 시나리오

---

## 시나리오 1: 멀티탭 동시 진입 (Public + Private)

### 1-1. 차트뷰 탭 (Public)
**동작**: KRW 마켓 전체 + BTC 호가

```python
# 코인 리스트: 모든 KRW 심볼 ticker
websocket_client.subscribe_ticker(
    component_id="chart_coin_list",
    symbols=all_krw_symbols,
    callback=update_chart_coin_list
)

# 호가창: KRW-BTC orderbook
websocket_client.subscribe_orderbook(
    component_id="chart_orderbook",
    symbols=["KRW-BTC"],
    callback=update_chart_orderbook
)
```

### 1-2. 거래내역 탭 (Public)
**동작**: 선택된 심볼의 체결내역

```python
# KRW-BTC 체결내역 구독
websocket_client.subscribe_trade(
    component_id="trade_history",
    symbols=["KRW-BTC"],
    callback=update_trade_history
)
```

### 1-3. 잔고 탭 (Private)
**동작**: 내 계좌 정보

```python
# 내 계좌 정보 구독 (Private WebSocket)
websocket_client.subscribe_my_account(
    component_id="account_balance",
    callback=update_account_balance
)
```

### 1-4. 주문 탭 (Private)
**동작**: 내 주문 현황

```python
# 내 주문 정보 구독 (Private WebSocket)
websocket_client.subscribe_my_order(
    component_id="order_status",
    callback=update_order_status
)
```

### 1-5. 통합 웹소켓 상태

**Public WebSocket 구독**:
```
- ticker: 모든 KRW 심볼 (chart_coin_list)
- orderbook: KRW-BTC (chart_orderbook)
- trade: KRW-BTC (trade_history)
```

**Private WebSocket 구독**:
```
- myAccount: 계좌 정보 (account_balance)
- myOrder: 주문 정보 (order_status)
```

**예상 Public 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "...모든_KRW_심볼"]
  },
  {
    "ticket": "public_ticket",
    "type": "orderbook",
    "codes": ["KRW-BTC"]
  },
  {
    "ticket": "public_ticket",
    "type": "trade",
    "codes": ["KRW-BTC"]
  }
]
```

**예상 Private 메시지**:
```json
[
  {
    "ticket": "private_ticket",
    "type": "myAccount"
  },
  {
    "ticket": "private_ticket",
    "type": "myOrder"
  }
]
```

---

## 시나리오 2: 심볼 변경 연쇄 반응

### 2-1. 차트뷰에서 KRW-ETH 선택
**동작**: 호가창 심볼 변경 → 거래내역도 연동 변경

```python
# 차트뷰 이벤트 발생
event_bus.emit("symbol_changed", {"old": "KRW-BTC", "new": "KRW-ETH"})

# 호가창 구독 변경
websocket_client.subscribe_orderbook(
    component_id="chart_orderbook",
    symbols=["KRW-ETH"],  # KRW-BTC → KRW-ETH
    callback=update_chart_orderbook
)

# 거래내역도 연동 변경
websocket_client.subscribe_trade(
    component_id="trade_history",
    symbols=["KRW-ETH"],  # KRW-BTC → KRW-ETH
    callback=update_trade_history
)
```

**변경된 Public 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "...모든_KRW_심볼"]
  },
  {
    "ticket": "public_ticket",
    "type": "orderbook",
    "codes": ["KRW-ETH"]
  },
  {
    "ticket": "public_ticket",
    "type": "trade",
    "codes": ["KRW-ETH"]
  }
]
```

---

## 시나리오 3: 스트림 타입 최적화

### 3-1. 차트뷰 + 알고리즘 트레이딩 동시 실행
**동작**: UI는 snapshot+realtime, 알고리즘은 realtime만

```python
# 차트뷰: 즉시 표시용 (snapshot + realtime)
websocket_client.subscribe_ticker(
    component_id="chart_display",
    symbols=["KRW-BTC"],
    callback=update_chart_ui
)

# 알고리즘: 실시간 분석용 (realtime만)
websocket_client.subscribe_ticker(
    component_id="algo_engine",
    symbols=["KRW-BTC"],
    is_only_realtime=True,  # snapshot 불필요
    callback=process_algo_signal
)
```

### 3-2. 구독 복잡성 처리
**문제**: 같은 심볼에 다른 스트림 타입 요구

**SubscriptionManager 내부 처리**:
1. **복잡성 감지**: KRW-BTC ticker (snapshot+realtime vs realtime)
2. **통합 전략**: 포괄적 구독으로 통합 (기본값: snapshot + realtime)
3. **데이터 분리**: 수신 시 컴포넌트별 스트림 타입 필터링 적용

**최종 메시지** (통합 방식):
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC"]
  }
]
```

**수신 데이터 처리**:
- **chart_display**: SNAPSHOT + REALTIME 모두 사용
- **algo_engine**: SNAPSHOT 무시, REALTIME만 사용 (stream_type 필터링)

**메시지 최적화 원칙**:
- **기본값**: `isOnlySnapshot: false`, `isOnlyRealtime: false` → 필드 생략
- **명시적 옵션**: realtime만 필요한 경우에만 `"isOnlyRealtime": true` 추가
- **snapshot만**: `"isOnlySnapshot": true` 추가 (일회성 조회)

---

## 시나리오 4: 탭 닫기 & 구독 정리

### 4-1. 거래내역 탭 닫기
**동작**: trade 구독만 제거, 다른 구독 유지

```python
# 거래내역 컴포넌트 해제
await websocket_client.unsubscribe_component("trade_history")
```

**정리된 Public 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "...모든_KRW_심볼"]
  },
  {
    "ticket": "public_ticket",
    "type": "orderbook",
    "codes": ["KRW-ETH"]
  }
]
```

### 4-2. 모든 차트뷰 탭 닫기
**동작**: Public 구독 대부분 정리, Private는 유지

```python
# 차트 관련 컴포넌트 모두 해제
await websocket_client.unsubscribe_component("chart_coin_list")
await websocket_client.unsubscribe_component("chart_orderbook")
```

**최종 Public 메시지** (빈 구독):
```json
[]
```

**Private 메시지** (유지):
```json
[
  {
    "ticket": "private_ticket",
    "type": "myAccount"
  },
  {
    "ticket": "private_ticket",
    "type": "myOrder"
  }
]
```

---

## 시나리오 3-3: 스트림 타입 충돌 해결
**문제 상황**: 같은 심볼에 다른 스트림 타입 요구

```python
# 서브시스템1: 실시간 모니터링 (기본값: snapshot + realtime)
websocket_client.subscribe_ticker(
    component_id="realtime_monitor",
    symbols=["KRW-BTC", "KRW-ETH"],
    callback=update_realtime_monitor
)

# 서브시스템2: 현재가 조회 (snapshot만)
websocket_client.subscribe_ticker(
    component_id="price_checker",
    symbols=["KRW-BTC"],
    is_only_snapshot=True,
    callback=check_current_price
)
```

**SubscriptionManager 충돌 해결**:
1. **충돌 감지**: KRW-BTC ticker에 서로 다른 스트림 타입 요구
   - 시스템1: snapshot + realtime (기본값)
   - 시스템2: snapshot만
2. **통합 전략**: 포괄적 타입 선택 (snapshot + realtime)
3. **클라이언트 필터링**: 각 컴포넌트가 필요한 stream_type만 처리

**최종 통합 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH"]
  }
]
```

**수신 데이터 분리**:
- **realtime_monitor**: 모든 데이터 사용 (SNAPSHOT + REALTIME)
- **price_checker**: SNAPSHOT만 필터링하여 사용 (stream_type === "SNAPSHOT")

**충돌 해결 원칙**:
- **기본값 우선**: 기본값(snapshot + realtime)이 가장 포괄적
- **제한적 → 포괄적**: `snapshot만` + `realtime만` = `snapshot + realtime`
- **필터링 적용**: 각 컴포넌트는 필요한 데이터만 처리

---

## 시나리오 6: 실시간 스트림 보호 (고급 충돌 해결)

### **상황**: 이미 활성화된 realtime 스트림에 새로운 요구사항 추가

```python
# 1단계: 서브시스템1이 realtime만 구독 중
websocket_client.subscribe_ticker(
    component_id="realtime_monitor",
    symbols=["KRW-BTC", "KRW-ETH"],
    is_only_realtime=True,  # realtime만 구독 중
    callback=update_realtime_data
)

# 현재 활성 메시지:
# [{"ticket": "public_ticket", "type": "ticker", "codes": ["KRW-BTC", "KRW-ETH"], "isOnlyRealtime": true}]

# 2단계: 서브시스템2가 KRW-BTC snapshot 요청
websocket_client.subscribe_ticker(
    component_id="price_checker",
    symbols=["KRW-BTC"],
    is_only_snapshot=True,  # snapshot만 필요
    callback=check_current_price
)
```

### **SubscriptionManager 충돌 해결 로직**:

**문제 분석**:
- **KRW-BTC**: realtime 진행 중 + snapshot 요청 추가
- **KRW-ETH**: realtime만 유지

**해결 전략**: 심볼별 개별 최적화
1. **KRW-BTC**: realtime + snapshot 요구 → 기본값으로 업그레이드
2. **KRW-ETH**: realtime만 유지 → 기존 옵션 보존

### **최종 통합 메시지** (realtime 스트림 보호):
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC"]
    // 기본값 (snapshot + realtime) - 두 요구사항 모두 충족
  },
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-ETH"],
    "isOnlyRealtime": true
    // 기존 realtime 스트림 유지
  }
]
```

### **수신 데이터 처리**:
- **realtime_monitor**:
  - KRW-BTC: REALTIME만 사용 (SNAPSHOT 무시)
  - KRW-ETH: REALTIME 사용
- **price_checker**:
  - KRW-BTC: SNAPSHOT만 사용 (REALTIME 무시)

### **핵심 원칙**:
1. **기존 스트림 보호**: 활성 realtime 스트림은 절대 끊지 않음
2. **심볼별 최적화**: 각 심볼마다 최적의 스트림 타입 결정
3. **클라이언트 필터링**: 각 컴포넌트는 필요한 stream_type만 처리

---

## 고급 시나리오: 대량 심볼 관리

### 시나리오 5: 전체 마켓 모니터링
**요구사항**: KRW(200개) + BTC(100개) + USDT(50개) 심볼 동시 ticker 구독

```python
# 대용량 구독 (350개 심볼 - 한 번에 처리)
all_symbols = krw_symbols + btc_symbols + usdt_symbols

websocket_client.subscribe_ticker(
    component_id="market_scanner",
    symbols=all_symbols,
    callback=process_market_data
)
```

**대용량 처리 특징**:
- **단일 메시지**: 350개 심볼을 하나의 메시지로 전송
- **업비트 검증완료**: `demo_upbit_websocket_full_snapshot.py`에서 전체 마켓 처리 검증됨
- **배치 분할 불필요**: 불필요한 복잡성 및 오버헤드 제거

**통합 메시지** (단일 요청):
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "BTC-ETH", "BTC-XRP", "USDT-BTC", "USDT-ETH", "...전체_350개_심볼"]
  }
]
```---

## 핵심 특징 분석

### 🔄 **연쇄 반응 관리**
- 심볼 변경 시 관련 컴포넌트 자동 연동
- 이벤트 버스를 통한 느슨한 결합

### 🔐 **Public/Private 분리**
- 인증이 필요한 데이터는 별도 연결
- 연결 실패 시 서로 영향 없음

### ⚡ **스트림 타입 최적화**
- 컴포넌트별 요구사항에 따른 데이터 필터링
- 복잡성 해결 시 포괄적 구독 선택

### 🧹 **자동 정리**
- 컴포넌트 해제 시 불필요한 구독 자동 제거
- WeakRef 기반 메모리 누수 방지

### 📊 **대용량 처리**
- 단일 메시지로 대량 심볼 처리 (검증완료)
- 불필요한 배치 분할 없이 효율적 전송
