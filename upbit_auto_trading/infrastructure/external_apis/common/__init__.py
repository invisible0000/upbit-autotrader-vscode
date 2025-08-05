"""Infrastructure Layer 외부 API 클라이언트 공통 모듈

이 모듈은 다양한 외부 API 클라이언트들의 공통 기반 클래스와 유틸리티를 제공합니다.
Rate Limiting, 인증, 재시도 로직 등의 공통 기능을 추상화하여
각 API 클라이언트 구현체에서 재사용할 수 있도록 합니다.

주요 클래스:
- BaseApiClient: 모든 API 클라이언트의 기본 클래스
- RateLimiter: API 속도 제한 관리
- RateLimitConfig: 속도 제한 설정
- ApiResponse: API 응답 표준화
- ApiClientError: API 클라이언트 예외
"""

from .api_client_base import (
    BaseApiClient,
    RateLimiter,
    RateLimitConfig,
    ApiResponse,
    ApiClientError
)

__all__ = [
    'BaseApiClient',
    'RateLimiter',
    'RateLimitConfig',
    'ApiResponse',
    'ApiClientError'
]
