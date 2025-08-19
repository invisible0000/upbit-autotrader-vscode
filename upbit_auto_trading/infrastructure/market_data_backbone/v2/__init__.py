"""
통합 마켓 데이터 백본 시스템 V2
Progressive Evolution을 통한 단계적 구현
"""

from .market_data_backbone import MarketDataBackbone, TickerData, ChannelStrategy
from .data_unifier import DataUnifier, DataNormalizer, IntelligentCache, DataSource, DataQuality, NormalizedTickerData
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
    "ChannelRouter"
]

__version__ = "1.1.0"  # Phase 1.1 버전
