"""
Smart Routing 인터페이스

완전히 추상화된 데이터 라우터 인터페이스를 제공합니다.
기존 IDataRouter와 호환되면서도 개선된 구조입니다.
"""

from .data_router import IDataRouter
from .data_provider import IDataProvider

__all__ = [
    "IDataRouter",
    "IDataProvider"
]
