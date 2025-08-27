"""
업비트 WebSocket v5.0 - Public/Private 분리 아키텍처

🎯 주요 개선사항:
- Public/Private 클라이언트 분리
- 효율적인 티켓 관리 (Public: 3개, Private: 2개)
- Pydantic 데이터 검증
- YAML 외부 설정
- 명시적 상태 관리
- 사용자 정의 예외
- 이벤트 기반 아키텍처

🔧 사용법:
```python
# Public 클라이언트
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import UpbitWebSocketPublicV5

client = UpbitWebSocketPublicV5()
await client.connect()
await client.subscribe_ticker(["KRW-BTC"])

# Private 클라이언트
from upbit_auto_trading.infrastructure.external_apis.upbit.websocket_v5 import UpbitWebSocketPrivateV5

private_client = UpbitWebSocketPrivateV5()
await private_client.connect()
await private_client.subscribe_my_orders()
```
"""

__version__ = "5.0.0"

# Public/Private 클라이언트
from .upbit_websocket_public_client import UpbitWebSocketPublicV5, create_public_client
from .upbit_websocket_private_client import UpbitWebSocketPrivateV5, create_private_client

# 공용 모델
from .models import (
    WebSocketMessage, TickerData, TradeData, OrderbookData, CandleData,
    SubscriptionRequest, ConnectionStatus, MessageType
)

# 설정 및 상태
from .config import WebSocketConfig, load_config
from .state import WebSocketState, WebSocketStateMachine

# 예외
from .exceptions import (
    WebSocketError, WebSocketConnectionError, SubscriptionError,
    MessageParsingError, ConfigurationError, InvalidAPIKeysError,
    TooManySubscriptionsError
)

__all__ = [
    # Public/Private 클라이언트
    "UpbitWebSocketPublicV5",
    "UpbitWebSocketPrivateV5",
    "create_public_client",
    "create_private_client",    # 데이터 모델
    "WebSocketMessage",
    "TickerData",
    "TradeData",
    "OrderbookData",
    "CandleData",
    "SubscriptionRequest",
    "ConnectionStatus",
    "MessageType",

    # 설정
    "WebSocketConfig",
    "load_config",

    # 상태 관리
    "WebSocketState",
    "WebSocketStateMachine",

    # 예외
    "WebSocketError",
    "WebSocketConnectionError",
    "SubscriptionError",
    "MessageParsingError",
    "ConfigurationError",
    "InvalidAPIKeysError",
    "TooManySubscriptionsError",
]
