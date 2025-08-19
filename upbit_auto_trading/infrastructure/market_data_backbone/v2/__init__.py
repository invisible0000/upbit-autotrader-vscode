"""
통합 마켓 데이터 백본 시스템 V2
Progressive Evolution을 통한 단계적 구현 + 파일 분리 완료
"""

from .market_data_backbone import MarketDataBackbone, TickerData, ChannelStrategy
from .data_unifier import DataUnifier, IntelligentCache
from .data_normalizer import DataNormalizer
from .data_models import DataSource, DataQuality, NormalizedTickerData
from .unified_market_data_api import UnifiedMarketDataAPI, UnifiedTickerData
from .smart_channel_router import SmartChannelRouter
from .channel_router import ChannelRouter

__all__ = [
    "MarketDataBackbone",
    "TickerData",
    "ChannelStrategy",
    "DataUnifier",
    "DataNormalizer",
    "IntelligentCache",
    "DataSource",
    "DataQuality",
    "NormalizedTickerData",
    "UnifiedMarketDataAPI",
    "UnifiedTickerData",
    "SmartChannelRouter",
    "ChannelRouter"
]

__version__ = "2.1.0"  # Phase 2.1 + 파일 분리 완료
