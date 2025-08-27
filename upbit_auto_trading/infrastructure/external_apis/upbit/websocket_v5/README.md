# 업비트 WebSocket v5.0 - Clean Slate Architecture

## 🎯 개요

업비트 WebSocket v5.0은 기존 레거시 코드를 완전히 제거하고 현대적인 Python 패턴으로 새롭게 구현한 "Clean Slate" 아키텍처입니다.

### 주요 개선사항

- **Pydantic 데이터 검증**: 타입 안전성과 데이터 유효성 검증
- **YAML 외부 설정**: 하드코딩 제거, 유연한 설정 관리
- **명시적 상태 관리**: State Machine 패턴으로 명확한 상태 제어
- **사용자 정의 예외**: 구체적인 오류 정보와 복구 힌트
- **이벤트 기반 아키텍처**: 외부 시스템과의 느슨한 결합

## 📊 코드 복잡도 비교

| 버전 | 파일 수 | 총 라인 수 | 복잡도 |
|------|---------|------------|---------|
| 기존 | 2개 | 1,724줄 | 높음 |
| v5.0 | 6개 | ~1,000줄 | 낮음 |

**42% 코드 감소** 📉

## 🏗️ 아키텍처 구조

```
websocket_v5/
├── __init__.py          # 공용 API 정의
├── client.py           # 메인 WebSocket 클라이언트
├── models.py           # Pydantic 데이터 모델
├── config.py           # YAML 설정 시스템
├── state.py            # State Machine 패턴
├── exceptions.py       # 사용자 정의 예외
├── websocket_config.yaml  # 기본 설정 파일
├── examples.py         # 사용 예제
└── README.md           # 이 파일
```

## 🚀 빠른 시작

### 1. 기본 사용법

```python
import asyncio
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import UpbitWebSocketV5

async def main():
    # 클라이언트 생성 및 연결
    client = UpbitWebSocketV5()
    await client.connect()

    # 데이터 수신 콜백
    def on_ticker(data):
        print(f"{data.code}: {data.trade_price:,}원")

    # 구독
    subscription_id = await client.subscribe("ticker", ["KRW-BTC"], on_ticker)

    # 30초 대기
    await asyncio.sleep(30)

    # 정리
    await client.unsubscribe(subscription_id)
    await client.disconnect()

asyncio.run(main())
```

### 2. 설정 파일 사용

```python
# custom_config.yaml 파일 생성 후
client = UpbitWebSocketV5(config_path="custom_config.yaml")
```

### 3. 빠른 구독 (개발/테스트용)

```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import quick_subscribe

def callback(data):
    print(f"가격: {data.trade_price:,}원")

client = await quick_subscribe("ticker", ["KRW-BTC"], callback)
```

## 📋 지원 데이터 타입

| 타입 | 설명 | 모델 클래스 |
|------|------|-------------|
| `ticker` | 현재가 정보 | `TickerData` |
| `trade` | 체결 정보 | `TradeData` |
| `orderbook` | 호가 정보 | `OrderbookData` |
| `candle` | 캔들 정보 | `CandleData` |

## ⚙️ 설정

### 기본 설정 파일 구조

```yaml
connection:
  url: "wss://api.upbit.com/websocket/v1"
  connection_timeout: 10.0
  ping_interval: 20.0
  heartbeat_timeout: 60.0

reconnection:
  enabled: true
  max_attempts: 5
  base_delay: 2.0

subscription:
  max_subscriptions: 10
  batch_size: 5

performance:
  message_buffer_size: 1000
  max_memory_mb: 100.0

logging:
  level: "INFO"
  enable_debug: false
```

## 🔄 상태 관리

WebSocket 연결 상태가 명시적으로 관리됩니다:

```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import WebSocketState

# 가능한 상태들
WebSocketState.DISCONNECTED  # 연결 해제
WebSocketState.CONNECTING    # 연결 중
WebSocketState.CONNECTED     # 연결됨
WebSocketState.DISCONNECTING # 연결 해제 중
WebSocketState.ERROR         # 오류 상태

# 상태 확인
status = await client.get_status()
print(f"현재 상태: {status.state.value}")
print(f"수신 메시지: {status.message_count}개")
print(f"업타임: {status.uptime_seconds:.1f}초")
```

## 🚨 오류 처리

구체적인 예외 타입으로 정확한 오류 처리:

```python
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import (
    WebSocketConnectionError,
    SubscriptionError,
    MessageParsingError
)

try:
    await client.connect()
except WebSocketConnectionError as e:
    print(f"연결 실패: {e}")
    print(f"복구 액션: {e.recovery_action.value}")
    if e.can_retry():
        # 재시도 로직
        pass
```

## 🎯 이벤트 시스템

외부 이벤트 브로커와 연동 가능:

```python
class MyEventBroker:
    async def emit(self, event_type: str, data):
        print(f"이벤트: {event_type}")

event_broker = MyEventBroker()
client = UpbitWebSocketV5(event_broker=event_broker)

# 이벤트로 데이터 수신
# websocket.ticker, websocket.trade, websocket.connected 등
```

## 🧪 테스트

```bash
# 예제 실행
python examples.py

# 단위 테스트 (향후 구현)
pytest test_websocket_v5.py
```

## 📈 성능 특징

- **자동 재연결**: 네트워크 오류 시 지수 백오프로 재연결
- **메모리 관리**: 설정 가능한 메모리 한계와 버퍼 크기
- **타입 안전성**: Pydantic으로 런타임 데이터 검증
- **비동기 처리**: asyncio 기반 고성능 메시지 처리

## 🔧 고급 사용법

### 1. 여러 구독 관리

```python
# 여러 데이터 타입 동시 구독
ticker_sub = await client.subscribe("ticker", ["KRW-BTC", "KRW-ETH"])
trade_sub = await client.subscribe("trade", ["KRW-BTC"])
orderbook_sub = await client.subscribe("orderbook", ["KRW-BTC"])

# 선택적 구독 취소
await client.unsubscribe(ticker_sub)
```

### 2. 상태 기반 로직

```python
if client.is_connected():
    await client.subscribe("ticker", symbols)
else:
    await client.connect()
```

### 3. 오류 복구

```python
try:
    await client.subscribe("ticker", symbols)
except SubscriptionError as e:
    if e.should_reconnect():
        await client.disconnect()
        await client.connect()
        await client.subscribe("ticker", symbols)
```

## 🛠️ 개발자 노트

### 설계 원칙

1. **단일 책임 원칙**: 각 모듈은 하나의 명확한 역할
2. **의존성 역전**: 외부 설정과 이벤트 시스템 주입
3. **실패 처리**: 명시적 오류 타입과 복구 전략
4. **타입 안전성**: 컴파일 타임 및 런타임 타입 검증

### 확장 포인트

- `models.py`: 새로운 데이터 타입 추가
- `exceptions.py`: 사용자 정의 예외 추가
- `config.py`: 새로운 설정 섹션 추가
- `client.py`: 메시지 핸들러 확장

## 📄 라이선스

이 프로젝트는 기존 업비트 자동매매 시스템의 일부입니다.

---

**업비트 WebSocket v5.0** - 현대적이고 안정적인 실시간 데이터 수신 🚀
