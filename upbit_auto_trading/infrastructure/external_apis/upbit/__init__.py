"""Upbit API 클라이언트 모듈

이 모듈은 Upbit 거래소 API와의 연동을 담당하는 Infrastructure Layer 컴포넌트입니다.
업비트 전용으로 최적화된 단순하고 견고한 구조를 제공합니다.

주요 클래스:
- UpbitPublicClient: 공개 API 클라이언트 (인증 불필요)
- UpbitPrivateClient: 프라이빗 API 클라이언트 (인증 필요)
- UpbitWebSocketPublicClient: 공개 WebSocket 클라이언트 (시세 데이터)
- UpbitWebSocketPrivateClient: 프라이빗 WebSocket 클라이언트 (계좌/주문)
- UpbitAuthenticator: JWT 인증 관리
- UpbitRateLimiter: 업비트 전용 Rate Limiter

사용 예시:
```python
# 공개 데이터만 사용
client = UpbitPublicClient()
ticker = await client.get_ticker('KRW-BTC')
candles = await client.get_candle_minutes('KRW-BTC', unit=5, count=100)
await client.close()

# 계좌/주문 기능까지 사용
private_client = UpbitPrivateClient(access_key='your_key', secret_key='your_secret')
accounts = await private_client.get_accounts()
order = await private_client.place_order('KRW-BTC', 'bid', 'limit', price=50000000, volume=0.001)
await private_client.close()
```
"""

from .upbit_public_client import UpbitPublicClient, create_upbit_public_client
# from .upbit_private_client import UpbitPrivateClient, create_upbit_private_client
from .upbit_auth import UpbitAuthenticator
from .upbit_rate_limiter import (
    UpbitGCRARateLimiter, get_global_rate_limiter
)

# WebSocket v6 사용 (간소화된 아키텍처)
from .websocket.core.websocket_client import WebSocketClient as UpbitWebSocketClient
from .websocket.core.websocket_manager import get_websocket_manager as get_global_websocket_manager


# 호환성을 위한 별칭 (레거시 코드 지원)
def create_public_client():
    """공개 데이터용 WebSocket 클라이언트 생성"""
    return UpbitWebSocketClient(component_id="public_client")


def create_private_client():
    """개인 데이터용 WebSocket 클라이언트 생성"""
    return UpbitWebSocketClient(component_id="private_client")


UpbitWebSocketPublicClient = create_public_client
UpbitWebSocketPrivateClient = create_private_client

__all__ = [
    'UpbitPublicClient',
    # 'UpbitPrivateClient',
    'UpbitAuthenticator',
    'UpbitGCRARateLimiter',
    'create_upbit_public_client',
    # 'create_upbit_private_client',
    'get_global_rate_limiter',

    # WebSocket v6 (새로운 통합 API)
    'UpbitWebSocketClient',           # 새로운 프록시 API (권장)
    'get_global_websocket_manager',   # 고급 사용자용

    # WebSocket v6 (호환성 별칭)
    'UpbitWebSocketPublicClient',     # 레거시 호환성
    'UpbitWebSocketPrivateClient',    # 레거시 호환성
    'create_public_client',           # 직접 사용
    'create_private_client',          # 직접 사용
]
