"""Infrastructure Layer 외부 API 클라이언트 모듈

이 모듈은 외부 서비스와의 API 연동을 담당하는 Infrastructure Layer 컴포넌트입니다.
DDD(Domain-Driven Design) 아키텍처에서 Infrastructure Layer는 외부 시스템과의
의존성을 캡슐화하고 도메인 레이어에 깔끔한 인터페이스를 제공하는 역할을 합니다.

현재 지원하는 API:
- Upbit: 한국 암호화폐 거래소 API (공개/프라이빗 모두 지원)

향후 확장 가능한 API:
- Binance: 글로벌 암호화폐 거래소 API
- KIS: 한국투자증권 API
- 기타 거래소 및 금융 API

사용 예시:
```python
from upbit_auto_trading.infrastructure.external_apis.upbit import UpbitClient

# 비동기 컨텍스트 매니저 사용 (권장)
async with UpbitClient(access_key='key', secret_key='secret') as client:
    markets = await client.get_krw_markets()
    portfolio = await client.get_portfolio_with_prices()
```
"""

# 현재는 Upbit만 제공하지만, 향후 다른 거래소도 추가 가능
from .upbit import (
    UpbitPublicClient,
    UpbitPrivateClient,
    UpbitWebSocketQuotationClient,
    UpbitWebSocketPrivateClient,
    UpbitAuthenticator
)

from .common import (
    BaseApiClient,
    RateLimiter,
    RateLimitConfig,
    ApiResponse,
    ApiClientError
)

__all__ = [
    # Upbit API (4개 클라이언트 구조)
    'UpbitPublicClient',
    'UpbitPrivateClient',
    'UpbitWebSocketQuotationClient',
    'UpbitWebSocketPrivateClient',
    'UpbitAuthenticator',

    # 공통 기반 클래스
    'BaseApiClient',
    'RateLimiter',
    'RateLimitConfig',
    'ApiResponse',
    'ApiClientError'
]
