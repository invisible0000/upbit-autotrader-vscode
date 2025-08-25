"""
Smart Data Provider V4.0 - 패키지 초기화

Layer 1: API 인터페이스
Layer 2: 캐시 & 실시간 시스템
Layer 3: 데이터 관리

🎯 성능 목표: 500+ symbols/sec (27.1에서 18.5배 향상)
"""

from .smart_data_provider import SmartDataProvider, BatchRequestResult
from .market_data_models import DataResponse, Priority, PerformanceMetrics
from .market_data_cache import MarketDataCache
from .realtime_data_manager import RealtimeDataManager
from .market_data_manager import MarketDataManager

__version__ = "4.0.0"
__all__ = [
    # 메인 API
    "SmartDataProvider",
    "BatchRequestResult",

    # 핵심 모델
    "DataResponse",
    "Priority",
    "PerformanceMetrics",

    # Layer 시스템
    "MarketDataCache",      # Layer 2: 캐시 시스템
    "RealtimeDataManager",  # Layer 2: 실시간 관리
    "MarketDataManager",    # Layer 3: 데이터 관리
]

# 패키지 정보
PERFORMANCE_TARGET = 500  # symbols per second
ARCHITECTURE_LAYERS = 3
CONSOLIDATION_RATIO = 0.87  # 87% 복잡도 감소
