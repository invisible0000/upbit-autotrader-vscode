"""
Smart Routing 인터페이스 패키지

추상 인터페이스들을 정의하여 완전한 추상화를 제공합니다:
- IDataRouter: 메인 라우터 인터페이스
- IDataProvider: 거래소별 데이터 제공자 인터페이스
- 기타 보조 인터페이스들
"""

from .data_router import (
    IDataRouter,
    IRealtimeDataStream,
    IChannelSelector
)

from .data_provider import (
    IDataProvider,
    IFieldMapper,
    IRateLimiter,
    IConnectionManager,
    IErrorHandler,
    IDataValidator
)

__all__ = [
    # Core interfaces
    "IDataRouter",
    "IDataProvider",

    # Streaming interfaces
    "IRealtimeDataStream",

    # Strategy interfaces
    "IChannelSelector",

    # Provider support interfaces
    "IFieldMapper",
    "IRateLimiter",
    "IConnectionManager",
    "IErrorHandler",
    "IDataValidator",
]
