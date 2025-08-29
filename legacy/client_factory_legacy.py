"""
업비트 클라이언트 팩토리 - 단순화 버전

업비트 전용 클라이언트 생성을 위한 팩토리
"""
from typing import Optional

from .upbit_public_client import UpbitPublicClient
from .upbit_private_client import UpbitPrivateClient
from .upbit_rate_limiter import UpbitRateLimiter


class UpbitClientFactory:
    """업비트 클라이언트 팩토리"""

    @staticmethod
    def create_public_client(
        rate_limiter: Optional[UpbitRateLimiter] = None
        rate_limiter: Optional[Union[UniversalRateLimiter, EndpointRateLimiter]] = None
    ) -> UpbitPublicClient:
        """
        업비트 공개 API 클라이언트 생성

        Args:
            adapter: 업비트 어댑터 (기본값: 자동 생성)
            use_endpoint_limiter: 엔드포인트별 세밀한 Rate Limiting 사용 여부
            rate_limiter: 사용자 정의 Rate Limiter (기본값: 자동 생성)

        Returns:
            UpbitPublicClient: 설정된 Rate Limiter를 사용하는 클라이언트
        """
        if adapter is None:
            adapter = UpbitAdapter()

        if rate_limiter is None:
            if use_endpoint_limiter:
                # 엔드포인트별 세밀한 Rate Limiting 사용
                rate_limiter = create_upbit_endpoint_limiter("upbit_public_endpoint")
            else:
                # 기존 단순한 Rate Limiting 사용
                config = ExchangeRateLimitConfig.for_upbit_public()
                rate_limiter = UniversalRateLimiter(config)

        return UpbitPublicClient(adapter, rate_limiter)

    @staticmethod
    def create_private_client(
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        adapter: Optional[UpbitAdapter] = None,
        use_endpoint_limiter: bool = True,
        rate_limiter: Optional[Union[UniversalRateLimiter, EndpointRateLimiter]] = None
    ) -> UpbitPrivateClient:
        """
        업비트 프라이빗 API 클라이언트 생성

        Args:
            access_key: Upbit API Access Key
            secret_key: Upbit API Secret Key
            adapter: 업비트 어댑터 (기본값: 자동 생성)
            use_endpoint_limiter: 엔드포인트별 세밀한 Rate Limiting 사용 여부
            rate_limiter: 사용자 정의 Rate Limiter (기본값: 자동 생성)

        Returns:
            UpbitPrivateClient: 설정된 Rate Limiter를 사용하는 클라이언트
        """
        if adapter is None:
            adapter = UpbitAdapter()

        if rate_limiter is None:
            if use_endpoint_limiter:
                # 엔드포인트별 세밀한 Rate Limiting 사용
                rate_limiter = create_upbit_endpoint_limiter("upbit_private_endpoint")
            else:
                # 기존 단순한 Rate Limiting 사용
                config = ExchangeRateLimitConfig.for_upbit_private()
                rate_limiter = UniversalRateLimiter(config)

        return UpbitPrivateClient(access_key, secret_key, adapter, rate_limiter)


# 편의 함수들
def create_upbit_public_client_with_endpoint_limiter() -> UpbitPublicClient:
    """엔드포인트별 Rate Limiting을 사용하는 Public 클라이언트 생성"""
    return UpbitClientFactory.create_public_client(use_endpoint_limiter=True)


def create_upbit_private_client_with_endpoint_limiter(
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> UpbitPrivateClient:
    """엔드포인트별 Rate Limiting을 사용하는 Private 클라이언트 생성"""
    return UpbitClientFactory.create_private_client(
        access_key=access_key,
        secret_key=secret_key,
        use_endpoint_limiter=True
    )


def create_upbit_public_client_legacy() -> UpbitPublicClient:
    """기존 방식의 단순한 Rate Limiting을 사용하는 Public 클라이언트 생성"""
    return UpbitClientFactory.create_public_client(use_endpoint_limiter=False)


def create_upbit_private_client_legacy(
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> UpbitPrivateClient:
    """기존 방식의 단순한 Rate Limiting을 사용하는 Private 클라이언트 생성"""
    return UpbitClientFactory.create_private_client(
        access_key=access_key,
        secret_key=secret_key,
        use_endpoint_limiter=False
    )
