"""Upbit API 클라이언트 모듈

이 모듈은 Upbit 거래소 API와의 연동을 담당하는 Infrastructure Layer 컴포넌트입니다.
DDD 원칙에 따라 외부 API와의 의존성을 캡슐화하고 도메인 레이어에 깔끔한 인터페이스를 제공합니다.

주요 클래스:
- UpbitClient: 통합 API 클라이언트 (퍼블릭 + 프라이빗)
- UpbitPublicClient: 공개 API 클라이언트 (마켓 데이터 등)
- UpbitPrivateClient: 프라이빗 API 클라이언트 (계좌, 주문 등)
- UpbitAuthenticator: JWT 인증 관리

사용 예시:
```python
# 공개 데이터만 사용
async with UpbitClient() as client:
    markets = await client.get_krw_markets()
    candles = await client.get_candles_minutes('KRW-BTC', unit=5, count=100)

# 계좌/주문 기능까지 사용
async with UpbitClient(access_key='your_key', secret_key='your_secret') as client:
    accounts = await client.get_accounts()
    order = await client.place_limit_buy_order('KRW-BTC', price=50000000, volume=0.001)
```
"""

from .upbit_client import UpbitClient
from .upbit_public_client import UpbitPublicClient
from .upbit_private_client import UpbitPrivateClient
from .upbit_auth import UpbitAuthenticator

__all__ = [
    'UpbitClient',
    'UpbitPublicClient',
    'UpbitPrivateClient',
    'UpbitAuthenticator'
]
