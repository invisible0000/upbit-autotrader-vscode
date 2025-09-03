# 웹소켓 구독 시나리오 01: 차트뷰 기본 동작

## 개요
차트뷰 탭 최초 진입 시 기본 구독 동작과 코인 선택 시 구독 변경 시나리오

---

## 시나리오 1: 차트뷰 탭 최초 진입

### 1-1. 코인 리스트 구독
**동작**: 마켓 콤보박스 기본값(KRW) → KRW 마켓 리스트 조회 → 티커 구독

```python
# REST API로 마켓 리스트 조회
krw_markets = rest_client.get_market_list(market="KRW")
symbols = [market.symbol for market in krw_markets]

# 웹소켓 구독 (기본값: snapshot + realtime)
websocket_client.subscribe_ticker(
    component_id="coin_list",
    symbols=symbols,
    callback=update_coin_list
)
```

**결과**:
- 즉시 스냅샷 수신 → 코인 리스트 초기 표시
- 이후 실시간 스트림 → 코인 리스트 실시간 갱신

### 1-2. 호가창 구독
**동작**: 기본 심볼(KRW-BTC) → 호가 구독

```python
# 기본 심볼 호가 구독 (기본값: 30호가, snapshot + realtime)
websocket_client.subscribe_orderbook(
    component_id="orderbook",
    symbols=["KRW-BTC"],
    callback=update_orderbook
)
```

**결과**:
- 즉시 스냅샷 수신 → 호가창 초기 표시
- 이후 실시간 스트림 → 호가창 실시간 갱신

### 1-3. 통합 웹소켓 상태

**활성 구독**:
```
- ticker: 모든 KRW 시장 심벌 (snapshot + realtime)
- orderbook: KRW-BTC (snapshot + realtime)
```

**예상 통합 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "KRW-XRP", "...모든_KRW_심볼"]
  },
  {
    "ticket": "public_ticket",
    "type": "orderbook",
    "codes": ["KRW-BTC"]
  }
]
```---

## 시나리오 2: 코인 리스트에서 KRW-ETH 클릭

### 2-1. 코인 리스트 동작
**동작**: 기존 티커 구독 유지 (변경 없음)

```python
# 구독 변경 없음 - 이미 모든 KRW 심볼 구독 중
# 내부 이벤트만 발생
event_bus.emit("coin_selected", {"symbol": "KRW-ETH"})
```

### 2-2. 호가창 동작
**동작**: 기존 구독 해지 → 새 심볼 구독

```python
# 기존 호가창 구독 업데이트
websocket_client.subscribe_orderbook(
    component_id="orderbook",
    symbols=["KRW-ETH"],  # KRW-BTC → KRW-ETH 변경
    callback=update_orderbook
)
```

**내부 처리**:
1. SubscriptionManager가 변경 감지
2. KRW-BTC orderbook 구독 제거
3. KRW-ETH orderbook 구독 추가
4. 통합 메시지 재전송

### 2-3. 통합 웹소켓 상태

**활성 구독**:
```
- ticker: 모든 KRW 시장 심볼 (변경 없음)
- orderbook: KRW-ETH (KRW-BTC에서 변경)
```

**예상 통합 메시지**:
```json
[
  {
    "ticket": "public_ticket",
    "type": "ticker",
    "codes": ["KRW-BTC", "KRW-ETH", "KRW-XRP", "...모든_KRW_심볼"]
  },
  {
    "ticket": "public_ticket",
    "type": "orderbook",
    "codes": ["KRW-ETH"]
  }
]
```

---

## 핵심 특징

### 효율적 구독 관리
- **ticker**: 전체 구독 유지로 개별 코인 클릭 시 추가 요청 불필요
- **orderbook**: 단일 심볼만 구독하여 불필요한 데이터 수신 방지

### 실시간 데이터 흐름
1. **스냅샷**: 초기 데이터 즉시 표시
2. **실시간**: 지속적인 데이터 갱신
3. **구독 변경**: 컴포넌트별 독립적 관리

### WebSocket v6 특징 활용
- **컴포넌트 기반**: 각 UI 요소가 독립적으로 구독 관리
- **자동 통합**: SubscriptionManager가 중복 제거 및 최적화
- **상태 추적**: 구독 변경 시 효율적인 메시지 재전송
