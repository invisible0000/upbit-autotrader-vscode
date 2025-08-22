"""
Infrastructure Layer - 외부 시스템 연동 및 데이터 영속성

이 패키지는 DDD(Domain-Driven Design) 아키텍처의 Infrastructure Layer를 구현합니다.
Domain Layer에서 정의한 Repository 인터페이스들을 실제 기술 스택으로 구현하고,
외부 시스템(데이터베이스, API, 파일 시스템 등)과의 연동을 담당합니다.

주요 구성요소:
- repositories/: Domain Repository 인터페이스의 구현체들
- database/: 데이터베이스 연결 및 관리
- external_apis/: 외부 API 클라이언트 (Upbit 등)
- mappers/: Domain Entity와 Database Record 간 변환
- messaging/: 이벤트 메시징 시스템 (향후 확장)

사용 예시:
```python
from upbit_auto_trading.infrastructure.external_apis import UpbitClient

# 비동기 컨텍스트 매니저 사용
async with UpbitClient(access_key='key', secret_key='secret') as client:
    markets = await client.get_krw_markets()
```
"""

# 기존 imports 유지
from .repositories.repository_container import RepositoryContainer
from .database.database_manager import DatabaseManager, DatabaseConnectionProvider

# 새로운 외부 API 클라이언트 추가
try:
    from .external_apis import (
        UpbitPublicClient,
        UpbitPrivateClient,
        UpbitWebSocketQuotationClient,
        UpbitWebSocketPrivateClient,
        UpbitAuthenticator,
        BaseApiClient,
        RateLimiter,
        RateLimitConfig,
        ApiResponse,
        ApiClientError
    )

    __all__ = [
        'RepositoryContainer',
        'DatabaseManager',
        'DatabaseConnectionProvider',
        'UpbitPublicClient',
        'UpbitPrivateClient',
        'UpbitWebSocketQuotationClient',
        'UpbitWebSocketPrivateClient',
        'UpbitAuthenticator',
        'BaseApiClient',
        'RateLimiter',
        'RateLimitConfig',
        'ApiResponse',
        'ApiClientError'
    ]

except ImportError:
    # 외부 API 클라이언트가 없는 경우 기본만 제공
    __all__ = [
        'RepositoryContainer',
        'DatabaseManager',
        'DatabaseConnectionProvider'
    ]
