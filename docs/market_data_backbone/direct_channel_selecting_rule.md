채널 선택기를 거치지 않고 바로 채널이 결정되는 경우들을 조사해보겠습니다. 먼저 관련 코드를 살펴보겠습니다. models.py 파일에서 고정 채널 규칙을 확인해보겠습니다. 이제 Channel Selector가 고정 채널을 어떻게 확인하는지 다시 살펴보겠습니다. 이제 Smart Router에서 이 Channel Selector를 어떻게 사용하는지 확인해보겠습니다. Smart Router의 채널 선택 부분을 확인해보겠습니다. 이제 전체적인 채널 선택 흐름을 이해했습니다. 추가로 다른 컴포넌트에서 직접 채널을 지정하는 경우가 있는지 확인해보겠습니다. 더 정확한 조사를 위해 채널이 직접 지정되는 경우를 찾아보겠습니다. Channel Selector 내부의 채널 고정 로직을 더 자세히 살펴보겠습니다. ## 🔍 채널 선택기를 거치지 않는 고정 채널 규칙 조사 결과

### 📋 채널 선택 흐름 분석

코드베이스 조사 결과, 모든 요청은 **Channel Selector를 거치지만**, 다음과 같은 **고정 규칙**들이 스마트 선택보다 우선 적용됩니다:

### 🔒 1단계: WebSocket 제약 검증 (채널 선택기 내부)

**채널 선택기를 거치지만 즉시 REST 고정:**

```python
# 캔들 데이터 제약
if request.data_type == DataType.CANDLES:
    if request.to is not None:  # 과거 데이터 조회
        return ChannelDecision(
            channel=ChannelType.REST_API,
            reason="past_data_requires_rest",
            confidence=1.0
        )
    if request.count and request.count > 1:  # 다중 캔들
        return ChannelDecision(
            channel=ChannelType.REST_API,
            reason="multiple_candles_requires_rest",
            confidence=1.0
        )

# 체결 데이터 제약
elif request.data_type == DataType.TRADES:
    if request.to is not None:  # 과거 체결
        return ChannelDecision(
            channel=ChannelType.REST_API,
            reason="past_trades_requires_rest",
            confidence=1.0
        )
    if request.count and request.count > 1:  # 다중 체결
        return ChannelDecision(
            channel=ChannelType.REST_API,
            reason="multiple_trades_requires_rest",
            confidence=1.0
        )
```

### 🔒 2단계: API 제약사항 기반 고정 채널

**REST만 지원하는 데이터 타입 (models.py):**

```python
REST_ONLY_ENDPOINTS = {
    DataType.ACCOUNTS: EndpointConfig(
        fixed_channel=ChannelType.REST_API,
        description="계정 정보는 REST만 지원"
    ),
    DataType.ORDERS: EndpointConfig(
        fixed_channel=ChannelType.REST_API,
        description="주문 관리는 REST만 지원"
    ),
    DataType.DEPOSITS: EndpointConfig(
        fixed_channel=ChannelType.REST_API,
        description="입출금 내역은 REST만 지원"
    ),
    DataType.WITHDRAWS: EndpointConfig(
        fixed_channel=ChannelType.REST_API,
        description="출금 내역은 REST만 지원"
    )
}
```

### 🎯 3단계: 스마트 선택 알고리즘

**위 조건들에 해당하지 않는 경우만** 점수 기반 스마트 선택:

```python
# 유연한 채널 선택 (ticker, orderbook, trades, candles)
FLEXIBLE_ENDPOINTS = {
    DataType.TICKER: preferred_channel=ChannelType.WEBSOCKET,
    DataType.ORDERBOOK: preferred_channel=ChannelType.WEBSOCKET,
    DataType.TRADES: preferred_channel=ChannelType.WEBSOCKET,
    DataType.CANDLES: preferred_channel=ChannelType.WEBSOCKET
}
```

## 📊 실제 적용 예시

### ✅ 채널 선택기를 거치지만 즉시 결정되는 경우:

1. **계정 정보 조회** → 항상 REST API (`fixed_channel`)
2. **주문 관리** → 항상 REST API (`fixed_channel`)
3. **과거 캔들 데이터** → 항상 REST API (`past_data_requires_rest`)
4. **다중 캔들 요청** → 항상 REST API (`multiple_candles_requires_rest`)

### 🧠 스마트 선택이 적용되는 경우:

1. **실시간 티커** → 점수 계산으로 WebSocket/REST 결정
2. **실시간 호가** → 점수 계산으로 WebSocket/REST 결정
3. **단일 최신 캔들** → 점수 계산으로 WebSocket/REST 결정
4. **실시간 체결** → 점수 계산으로 WebSocket/REST 결정

## 🎯 결론

**모든 요청은 Channel Selector를 거치지만**, API 제약사항과 데이터 무결성을 위한 **고정 규칙들이 스마트 알고리즘보다 우선 적용**됩니다. 이는 시스템의 안정성과 데이터 정확성을 보장하기 위한 설계입니다! 🛡️
